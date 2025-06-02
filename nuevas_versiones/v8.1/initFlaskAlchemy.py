"""PROYECTO RII 2
   Run the API
"""

from modelsFlaskAlchemy import db, Robots
from apiFlaskAlchemy import create_api

api = create_api()
db.init_app(api)

# DEBUG Show all the routes
print(api.url_map)

with api.app_context():
    
    db.drop_all()

    db.create_all()

    # Dummy Robots
    root1 = Robots(robot_name="r1",robot_desc="First robot")
    root2 = Robots(robot_name="r2",robot_desc="Second robot")
    root3 = Robots(robot_name="r3",robot_desc="Third robot")
    db.session.add(root1)
    db.session.add(root2)
    db.session.add(root3)
    db.session.commit()


if __name__ == '__main__':
    api.run(port=5000, debug=False)