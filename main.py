# =========================================================
# APPLICATION ANDROID PYTHON (Kivy + Camera + HTTP Requests)
# Fichier: main.py
# =========================================================
import json
import time

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.network.urlrequest import UrlRequest

# Pour scanner avec la caméra sous Android nativement:
# Nécessite pyzbar et opencv-python ou plyer camera
try:
    from pyzbar.pyzbar import decode
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False


class DataMatrixScannerApp(App):
    def build(self):
        self.title = "Scanner DataMatrix Logistique"
        self.api_url = "https://api.mon-entreprise.com/v1/scan"

        main_layout = BoxLayout(orientation="vertical", padding=15, spacing=10)

        # Header
        main_layout.add_widget(
            Label(
                text="DATA MATRIX SCANNER (PYTHON)",
                font_size="20sp",
                bold=True,
                size_hint_y=None,
                height=40,
            )
        )

        # Datamatrix Read Output
        main_layout.add_widget(
            Label(text="Code DataMatrix Scanné :", size_hint_y=None, height=25)
        )
        self.code_input = TextInput(
            text="",
            multiline=False,
            font_size="18sp",
            size_hint_y=None,
            height=45,
        )
        main_layout.add_widget(self.code_input)

        # Quantity Input
        main_layout.add_widget(
            Label(text="Quantité :", size_hint_y=None, height=25)
        )
        qty_box = BoxLayout(
            orientation="horizontal", spacing=10, size_hint_y=None, height=50
        )

        btn_minus = Button(text="-", font_size="24sp", on_press=self.dec_qty)
        self.qty_input = TextInput(
            text="1", multiline=False, font_size="20sp", halign="center"
        )
        btn_plus = Button(text="+", font_size="24sp", on_press=self.inc_qty)

        qty_box.add_widget(btn_minus)
        qty_box.add_widget(self.qty_input)
        qty_box.add_widget(btn_plus)
        main_layout.add_widget(qty_box)

        # Status Label
        self.status_label = Label(
            text="Prêt à envoyer",
            color=(0.8, 0.8, 0.8, 1),
            size_hint_y=None,
            height=30,
        )
        main_layout.add_widget(self.status_label)

        # Submit Button
        btn_send = Button(
            text="ENVOYER LA REQUÊTE HTTP",
            background_color=(0.1, 0.7, 0.3, 1),
            font_size="16sp",
            bold=True,
            size_hint_y=None,
            height=60,
            on_press=self.send_http_request,
        )
        main_layout.add_widget(btn_send)

        return main_layout

    def inc_qty(self, instance):
        try:
            val = int(self.qty_input.text)
            self.qty_input.text = str(val + 1)
        except ValueError:
            self.qty_input.text = "1"

    def dec_qty(self, instance):
        try:
            val = int(self.qty_input.text)
            if val > 1:
                self.qty_input.text = str(val - 1)
        except ValueError:
            self.qty_input.text = "1"

    def send_http_request(self, instance):
        code = self.code_input.text.strip()
        qty = self.qty_input.text.strip()

        if not code:
            self.status_label.text = "Erreur : Code DataMatrix vide !"
            self.status_label.color = (1, 0.2, 0.2, 1)
            return

        payload = json.dumps(
            {
                "datamatrix": code,
                "quantity": int(qty) if qty.isdigit() else 1,
                "timestamp": int(time.time()),
                "device_id": "PYTHON-ANDROID-01",
            }
        )

        headers = {"Content-Type": "application/json"}

        self.status_label.text = "Envoi HTTP en cours..."
        self.status_label.color = (0.9, 0.7, 0.1, 1)

        # Requête asynchrone pour ne pas bloquer l'UI
        UrlRequest(
            self.api_url,
            req_body=payload,
            req_headers=headers,
            method="POST",
            on_success=self.on_http_success,
            on_error=self.on_http_error,
            on_failure=self.on_http_error,
        )

    def on_http_success(self, req, result):
        self.status_label.text = "Succès : Données transmises !"
        self.status_label.color = (0.2, 1, 0.3, 1)
        self.code_input.text = ""

    def on_http_error(self, req, result):
        self.status_label.text = f"Erreur HTTP : {req.resp_status}"
        self.status_label.color = (1, 0.2, 0.2, 1)


if __name__ == "__main__":
    DataMatrixScannerApp().run()
