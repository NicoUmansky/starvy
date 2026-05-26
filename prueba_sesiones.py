import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "Redis"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "mongoDB"))

from escrituras import registrar_usuario, login_usuario
from appRedis import verificar_sesion, cerrar_sesion
from mongo_client import usuarios_collection


class TestSesionesActivas(unittest.TestCase):

    def setUp(self):
        print("\n→ Conectando a MongoDB...")
        usuarios_collection.delete_one({"username": "usuario_prueba"})
        registrar_usuario("prueba@starvy.com", "prueba123", "usuario_prueba", 99999999, "Usuario", "Prueba")
        print("→ Conectando a Redis...")

    def tearDown(self):
        usuarios_collection.delete_one({"username": "usuario_prueba"})
        print("→ Limpieza completada")

    def test_login_crea_sesion(self):
        user_id = login_usuario("usuario_prueba", "prueba123")
        self.assertIsNotNone(user_id, "El login debería devolver un user_id")
        self.assertTrue(verificar_sesion(user_id), "Debería haber sesión activa tras el login")

    def test_login_credenciales_incorrectas(self):
        user_id = login_usuario("usuario_prueba", "password_malo")
        self.assertIsNone(user_id, "Con credenciales incorrectas no debería crearse sesión")

    def test_cerrar_sesion(self):
        user_id = login_usuario("usuario_prueba", "prueba123")
        cerrar_sesion(user_id)
        self.assertFalse(verificar_sesion(user_id), "Después de cerrar sesión no debería existir")


if __name__ == "__main__":
    unittest.main(verbosity=2)
