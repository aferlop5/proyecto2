"""PROYECTO RII 2
   Client Calls
"""

from sqlalchemy.orm import Session
from modelsAlchemy import Robots

def test(session: Session) -> None:
    """Creates several dummy robots in the table.
        
       Args: 
            session: opened session.
    """
    # Dummy Robots
    root1 = Robots(robot_name="r1",robot_desc="First robot")
    root2 = Robots(robot_name="r2",robot_desc="Second robot")
    root3 = Robots(robot_name="r3",robot_desc="Third robot")
    session.add(root1)
    session.add(root2)
    session.add(root3)
    session.commit()

def listRobots(session: Session) -> None:
    """List the robots in the table.
        
       Args: 
            session: opened session.
    """
    robots = session.query(Robots).all()  # Get all robots
    for robot in robots:
      #print(robot.to_xml())
      #print(robot.to_json())
      print(f"Robot name: {robot.robot_name}, Description: {robot.robot_desc}")
  
def addRobot(session: Session) -> None:
    """Add a robot to the table.
        
        Args: 
            session: opened session.
    """
    robot_name = input("Name of robot: ")
    robot_desc = input("Description: ")
    added_robot = Robots(robot_name=robot_name,robot_desc=robot_desc)
    session.add(added_robot)
    session.commit()

def updateRobot(session: Session) -> None:
    """Update robot information in the table.
        
        Args: 
            session: opened session.
    """
    robot_name = input("Name of robot: ")
    robot = session.query(Robots).filter_by(robot_name=robot_name).first()
    if robot:
            robot_new_name = input("New name of robot: ")
            robot_desc = input("New description: ")
            robot.robot_name = robot_new_name
            robot.robot_desc = robot_desc
            #robot.update_json({"robot_name" : robot_new_name, "robot_desc" : robot_desc})
            session.commit()

def deleteRobot(session: Session) -> None:
    """Delete robot from the table.
        
        Args: 
            session: opened session.
    """
    robot_name = input("Name of robot: ")
    robot = session.query(Robots).filter_by(robot_name=robot_name).first()
    if robot:
            session.delete(robot)
            session.commit()
