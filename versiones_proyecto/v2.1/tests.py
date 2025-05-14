import unittest
from rest import app, socketio
import json

class RobotAPITests(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.socketio_test_client = socketio.test_client(app)
    
    def test_cinta_control(self):
        """Test control de la cinta transportadora"""
        # Test iniciar cinta
        response = self.app.post('/cinta/run',
                               json={'direccion': 'forward', 'velocidad': 50})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['estado'], 'RUN')
        
        # Verificar evento WebSocket
        received = self.socketio_test_client.get_received()
        self.assertTrue(any(event['name'] == 'cinta_update' for event in received))

        # Test detener cinta
        response = self.app.post('/cinta/stop')
        self.assertEqual(response.status_code, 200)
    
    def test_ventosa_control(self):
        """Test control de la ventosa"""
        # Test activar ventosa
        response = self.app.post('/control_ventosa',
                               json={'accion': 'activar'})
        self.assertEqual(response.status_code, 200)
        
        # Verificar evento WebSocket
        received = self.socketio_test_client.get_received()
        self.assertTrue(any(event['name'] == 'ventosa_update' for event in received))

        # Test desactivar ventosa
        response = self.app.post('/control_ventosa',
                               json={'accion': 'desactivar'})
        self.assertEqual(response.status_code, 200)
    
    def test_robot_movement(self):
        """Test movimiento del robot"""
        movement_data = {
            'x': 0,
            'y': 0,
            'z': 0,
            'roll': 0,
            'pitch': 0,
            'yaw': 0
        }
        response = self.app.post('/control_robot',
                               json=movement_data)
        self.assertEqual(response.status_code, 200)
        
        # Verificar evento WebSocket
        received = self.socketio_test_client.get_received()
        self.assertTrue(any(event['name'] == 'robot_position_update' for event in received))
    
    def test_sensor_monitoring(self):
        """Test monitoreo de sensores"""
        # Test sensor DI1
        response = self.app.post('/control_sensor_DI1')
        self.assertEqual(response.status_code, 200)
        
        # Test sensor DI5
        response = self.app.post('/control_sensor_DI5')
        self.assertEqual(response.status_code, 200)
        
        # Verificar eventos WebSocket de sensores
        received = self.socketio_test_client.get_received()
        self.assertTrue(any(event['name'] == 'sensor_update' for event in received))
    
    def test_auto_mode(self):
        """Test modo automático"""
        response = self.app.post('/auto',
                               json={'usuario_id': 'test_user'})
        self.assertEqual(response.status_code, 200)
        
        # Verificar evento WebSocket
        received = self.socketio_test_client.get_received()
        self.assertTrue(any(event['name'] == 'auto_complete' for event in received))

if __name__ == '__main__':
    unittest.main() 