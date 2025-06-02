"""PROYECTO RII 2
   Robots table in sqlAlchemy
"""

from sqlalchemy import Column, Text, String, Integer
from sqlalchemy.ext.declarative import declarative_base
import xmltodict

# Create the Base class
Base = declarative_base()

# Robot table model
class Robots(Base):
    """ This class models a column in the table Robots.
    """
    # Table name and columns
    __tablename__ = 'robots'
    robot_id = Column("id", Integer, primary_key=True)
    robot_name = Column("name", String(32), unique=True, nullable=False)
    robot_desc = Column("description", Text, nullable=True)

    def __init__(self, robot_name : str, robot_desc : str) -> None:
        """Adds a robot in the table.
        
        Args: 
            robot_name: name of the robot.
        """
        # We will automatically generate the new id
        self.robot_name = robot_name
        self.robot_desc = robot_desc

    def to_json(self) -> dict:
        """From robot to JSON.
        """
        resource = {
            "robot_id": self.robot_id,
            "robot_name": self.robot_name,
            "robot_desc" : self.robot_desc
        }
        return resource
    
    @staticmethod
    def from_json(data: dict) -> None:
        """From JSON to user.

        Args: 
            data: input JSON.
        """
        try:
            # all lower
            my_robot = data.get("robot_name").rstrip().lower()
            my_desc = data.get("robot_desc").rstrip()

            return Robots(robot_name = my_robot, robot_desc = my_desc)

        except KeyError:
            return None

        except IndexError:
            return None

    def to_xml(self) -> str:
        """From robot to XML.
        """
        xml_data = f"""
        <Robot>
            <robot_id>{self.robot_id}</robot_id>
            <robot_name>{self.robot_name}</robot_name>
            <robot_desc>{self.robot_desc}</robot_desc>
        </Robot>
        """
        return xml_data

    @staticmethod
    def from_xml(data: dict) -> None:
        """From XML to a new robot.

        Args: 
            data: XML as dict.
        """
        try:
            # all lower
            my_robot = data["Robot"]["robot_name"].rstrip().lower()
            my_desc = data["Robot"]["robot_desc"].rstrip()

            return Robots(robot_name = my_robot, robot_desc = my_desc)

        except KeyError:
            return None

        except IndexError:
            return None

    def update_xml(self, data: dict) -> None:
        """Update a robot from a XML.

        Args: 
            data: XML as dict.
        """
        data = xmltodict.parse(data)
        try:
            self.robot_name = data["Robot"]["robot_name"].rstrip().lower()
            self.robot_desc = data["Robot"]["robot_desc"].rstrip()
        except:
            pass


    def update_json(self, data: dict) -> None:
        """Update a robot from JSON.

        Args: 
            data: input JSON.
        """
        try:
            self.robot_name = data.get("robot_name").rstrip().lower()
            self.robot_desc = data.get("robot_desc").rstrip()
        except:
            pass
