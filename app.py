from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    redirect,
    url_for
)

import networkx as nx

from database import (
    init_db,
    add_event,
    get_unsynced_events,
    mark_all_synced,
    count_unsynced
)


app = Flask(__name__)

init_db()


# =========================================================
# SIMULATED CARBON INTENSITY DATA
# =========================================================

carbon_data = {

    "Region A": {
        "10:00": 400,
        "10:30": 350,
        "11:00": 220,
        "11:30": 180,
        "12:00": 300
    },

    "Region B": {
        "10:00": 250,
        "10:30": 180,
        "11:00": 150,
        "11:30": 200,
        "12:00": 280
    },

    "Region C": {
        "10:00": 320,
        "10:30": 300,
        "11:00": 280,
        "11:30": 350,
        "12:00": 400
    }
}


# =========================================================
# TASK CHARACTERIZATION
# =========================================================

def characterize_task(task_name, index):

    name = task_name.lower()

    if "research" in name:

        complexity = "Medium"
        model = "Medium Model"

    elif (
        "collect" in name
        or "retrieve" in name
        or "preprocess" in name
    ):

        complexity = "Easy"
        model = "Small Model"

    elif (
        "detect" in name
        or "analy" in name
        or "prediction" in name
    ):

        complexity = "Complex"
        model = "Large Model"

    elif (
        "report" in name
        or "generate" in name
    ):

        complexity = "Medium"
        model = "Medium Model"

    else:

        complexity = "Medium"
        model = "Medium Model"

    slack = 10 + (index * 5)

    deadline = 60

    return {

        "task": task_name,

        "complexity": complexity,

        "model": model,

        "slack": slack,

        "deadline": deadline

    }


# =========================================================
# DEPENDENCY-BASED DAG
# =========================================================

def create_dag(tasks):

    graph = nx.DiGraph()

    for task in tasks:

        graph.add_node(task)

    task_map = {
        task.lower(): task
        for task in tasks
    }

    def find_task(keyword):

        for name, original in task_map.items():

            if keyword in name:

                return original

        return None


    research = find_task("research")

    data_collection = find_task(
        "data collection"
    )

    image_preprocessing = find_task(
        "image preprocessing"
    )

    disease_detection = find_task(
        "disease detection"
    )

    soil_data = find_task(
        "soil data"
    )

    crop_health = find_task(
        "crop health"
    )

    yield_prediction = find_task(
        "yield prediction"
    )

    report = find_task("report")


    if research and data_collection:

        graph.add_edge(
            research,
            data_collection
        )


    if data_collection and image_preprocessing:

        graph.add_edge(
            data_collection,
            image_preprocessing
        )


    if data_collection and soil_data:

        graph.add_edge(
            data_collection,
            soil_data
        )


    if image_preprocessing and disease_detection:

        graph.add_edge(
            image_preprocessing,
            disease_detection
        )


    if disease_detection and crop_health:

        graph.add_edge(
            disease_detection,
            crop_health
        )


    if soil_data and crop_health:

        graph.add_edge(
            soil_data,
            crop_health
        )


    if crop_health and yield_prediction:

        graph.add_edge(
            crop_health,
            yield_prediction
        )


    if yield_prediction and report:

        graph.add_edge(
            yield_prediction,
            report
        )


    # Generic fallback
    if len(graph.edges()) == 0:

        for i in range(
            len(tasks) - 1
        ):

            graph.add_edge(
                tasks[i],
                tasks[i + 1]
            )


    return graph


# =========================================================
# MULTI-OBJECTIVE SCHEDULER
# =========================================================

def schedule_tasks(task_info):

    schedule = []

    available_times = [

        "10:00",
        "10:30",
        "11:00",
        "11:30",
        "12:00"

    ]

    model_cost = {

        "Small Model": 0.03,

        "Medium Model": 0.06,

        "Large Model": 0.12

    }

    model_latency = {

        "Small Model": 5,

        "Medium Model": 10,

        "Large Model": 20

    }


    for index, task in enumerate(task_info):

        selected_time = available_times[
            min(
                index,
                len(available_times) - 1
            )
        ]


        best_region = None

        lowest_carbon = float("inf")


        for region in carbon_data:

            carbon = carbon_data[
                region
            ][selected_time]


            if carbon < lowest_carbon:

                lowest_carbon = carbon

                best_region = region


        model = task["model"]


        schedule.append({

            "task":
                task["task"],

            "complexity":
                task["complexity"],

            "model":
                model,

            "region":
                best_region,

            "time":
                selected_time,

            "carbon":
                lowest_carbon,

            "cost":
                model_cost[model],

            "latency":
                model_latency[model],

            "slack":
                task["slack"],

            "deadline":
                task["deadline"]

        })


    return schedule


# =========================================================
# CLERK LOGIN PAGE
# =========================================================

@app.route("/login")
def login():

    return render_template(
        "login.html"
    )


# =========================================================
# SCHEDULER DASHBOARD
# =========================================================

@app.route("/scheduler")
def scheduler():

    return render_template(
        "index.html"
    )


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return redirect(
        url_for("login")
    )


# =========================================================
# GENERATE WORKFLOW
# =========================================================

@app.route(
    "/generate",
    methods=["POST"]
)
def generate():

    data = request.get_json() or {}

    workflow = data.get(
        "workflow",
        ""
    ).strip()


    if not workflow:

        return jsonify({

            "error":
                "Please enter a workflow."

        }), 400


    workflow = workflow.replace(
        "->",
        "→"
    )


    tasks = [

        task.strip()

        for task in workflow.split("→")

        if task.strip()

    ]


    if len(tasks) == 1:

        tasks = [

            "Research",

            "Data Collection",

            "Image Preprocessing",

            "Disease Detection",

            "Soil Data Collection",

            "Crop Health Analysis",

            "Yield Prediction",

            "Report Generation"

        ]


    graph = create_dag(tasks)


    task_info = []


    for index, task in enumerate(tasks):

        task_info.append(

            characterize_task(
                task,
                index
            )

        )


    schedule = schedule_tasks(
        task_info
    )


    total_carbon = sum(

        item["carbon"]

        for item in schedule

    )


    total_cost = sum(

        item["cost"]

        for item in schedule

    )


    total_latency = sum(

        item["latency"]

        for item in schedule

    )


    return jsonify({

        "tasks":
            tasks,

        "edges":
            list(graph.edges()),

        "task_info":
            task_info,

        "schedule":
            schedule,

        "metrics": {

            "carbon":
                total_carbon,

            "cost":
                round(
                    total_cost,
                    2
                ),

            "latency":
                total_latency

        }

    })


# =========================================================
# OFFLINE EVENT STORAGE
# =========================================================

@app.route(
    "/offline-event",
    methods=["POST"]
)
def offline_event():

    data = request.get_json() or {}

    task = data.get(
        "task",
        "Unknown Task"
    )

    status = data.get(
        "status",
        "Completed Offline"
    )


    add_event(

        "TASK_COMPLETED",

        task,

        status

    )


    return jsonify({

        "success":
            True,

        "pending":
            count_unsynced()

    })


# =========================================================
# GET PENDING OFFLINE EVENTS
# =========================================================

@app.route("/pending-events")
def pending_events():

    events = get_unsynced_events()

    result = []


    for event in events:

        result.append({

            "id":
                event[0],

            "type":
                event[1],

            "task":
                event[2],

            "status":
                event[3],

            "created_at":
                event[4]

        })


    return jsonify({

        "events":
            result,

        "count":
            len(result)

    })


# =========================================================
# AUTOMATIC SYNCHRONIZATION
# =========================================================

@app.route(
    "/sync",
    methods=["POST"]
)
def sync():

    events = get_unsynced_events()

    synchronized_count = len(events)

    mark_all_synced()


    return jsonify({

        "success":
            True,

        "synchronized":
            synchronized_count,

        "remaining":
            count_unsynced()

    })


# =========================================================
# DATABASE STATUS
# =========================================================

@app.route("/offline-status")
def offline_status():

    pending = count_unsynced()


    return jsonify({

        "pending":
            pending,

        "mode":

            "offline"
            if pending > 0
            else "online"

    })


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    return redirect(
        url_for("login")
    )


# =========================================================
# START SERVER
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )
  