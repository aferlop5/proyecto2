import time
import requests

API_URL = "http://localhost:5000/api/robots"
TIME_INTERVAL = 1  # seconds

# Esta función lee la lista de robots cada 10 segundos, si encuentra un robot
# cuyo nombre es "move_belt" imprime un mensaje y lo borra. Si encuentra un
# robot cuyo nombre es "stop_belt" imprime un mensaje y lo borra. En lugar de
# imprimir el mensaje, podéis conectarlo con vuestro ctrl.py (cada petición
# debería lanzarse en un hilo independiente)
def check_for_robots():
    try:
        response = requests.get(API_URL)

        if response.status_code == 200:
            all_robots = response.json()

            for robot in all_robots:
                #print(robot["robot_id"])
                # Check if robot_name is "move_belt"
                if (robot["robot_name"] == "move_belt"):
                    print("I'm activating the conveyor belt!")
                    remove_robot(robot["robot_id"])
                # Check if robot_name is "stop_belt"
                if (robot["robot_name"] == "stop_belt"):
                    print("I'm deactivating the conveyor belt!")
                    remove_robot(robot["robot_id"])
        else:
            print(f"API returned status: {response.status_code}")
    except Exception as e:
        print(f"Error checking API: {e}")

def remove_robot(robot_id):
    try:
        robot_resource_url = f"{API_URL}/{robot_id}"
        response = requests.delete(robot_resource_url)
        #print(robot_resource_url)
        if response.status_code == 204:
            print(f"Robot (command!) deleted successfully!")
    except Exception as e:
        print(f"Error checking API: {e}")

while True:
    check_for_robots()
    time.sleep(TIME_INTERVAL)
