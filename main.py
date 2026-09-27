# =========================================================
# APPLICATION ANDROID PYTHON (Kivy + Camera + HTTP Requests)
# Fichier: main.py
# Parse format GS1: 01{GTIN14}11{date AAMMJJ}10{lot}
# =========================================================
import json
import time
import re

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
        self.title = "Scanner DataMatrix OLFA"
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

        # Affichage des données parsées
        main_layout.add_widget(
            Label(text="Données parsées :", size_hint_y=None, height=25)
        )
        self.gtin_label = Label(
            text="GTIN-14 : -",
            font_size="14sp",
            size_hint_y=None,
            height=25,
            color=(0.2, 0.8, 1, 1),
        )
        main_layout.add_widget(self.gtin_label)

        self.date_label = Label(
            text="Date de fabrication : -",
            font_size="14sp",
            size_hint_y=None,
            height=25,
            color=(0.2, 0.8, 1, 1),
        )
        main_layout.add_widget(self.date_label)

        self.lot_label = Label(
            text="Lot : -",
            font_size="14sp",
            size_hint_y=None,
            height=25,
            color=(0.2, 0.8, 1, 1),
        )
        main_layout.add_widget(self.lot_label)

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

    def parse_datamatrix_gs1(self, code):
        """
        Parse le format GS1: 01{GTIN14}11{date AAMMJJ}10{lot}
        Retourne un dictionnaire avec gtin, date_fab, lot
        """
        data = {"gtin": None, "date_fab": None, "lot": None}

        # Pattern pour extraire GTIN-14 (01 + 14 digits)
        gtin_match = re.search(r"01(\d{14})", code)
        if gtin_match:
            data["gtin"] = gtin_match.group(1)

        # Pattern pour extraire date de fabrication (11 + AAMMJJ sur 6 digits)
        date_match = re.search(r"11(\d{6})", code)
        if date_match:
            date_str = date_match.group(1)
            # Format AAMMJJ -> JJ/MM/AA
            data["date_fab"] = f"{date_str[4:6]}/{date_str[2:4]}/{date_str[0:2]}"

        # Pattern pour extraire lot (10 + variable length)
        lot_match = re.search(r"10([^\d][^\d]*|[A-Z0-9]*?)(?=\d{2}|$)", code)
        if lot_match:
            lot_value = lot_match.group(1).strip()
            data["lot"] = lot_value if lot_value else None
        else:
            # Alternative: chercher "10" suivi de caractères jusqu'à fin ou prochain identifiant
            lot_match = re.search(r"10(.+?)(?=01|11|$)", code)
            if lot_match:
                data["lot"] = lot_match.group(1).strip()

        return data

    def update_parsed_display(self, code):
        """Affiche les données parsées à l'écran"""
        parsed = self.parse_datamatrix_gs1(code)

        self.gtin_label.text = f"GTIN-14 : {parsed['gtin'] or '-'}"
        self.date_label.text = f"Date de fabrication : {parsed['date_fab'] or '-'}"
        self.lot_label.text = f"Lot : {parsed['lot'] or '-'}"

        return parsed

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

        # Parser les données
        parsed = self.update_parsed_display(code)

        if not parsed["gtin"]:
            self.status_label.text = "Erreur : Format GS1 invalide (01 manquant) !"
            self.status_label.color = (1, 0.2, 0.2, 1)
            return

        # Construire le payload avec les 3 champs parsés
        payload = json.dumps(
            {
                "gtin": parsed["gtin"],
                "date_fabrication": parsed["date_fab"],
                "lot": parsed["lot"],
                "quantity": int(qty) if qty.isdigit() else 1,
                "timestamp": int(time.time()),
                "device_id": "PYTHON-ANDROID-01",
                "datamatrix_raw": code,
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
        self.gtin_label.text = "GTIN-14 : -"
        self.date_label.text = "Date de fabrication : -"
        self.lot_label.text = "Lot : -"

    def on_http_error(self, req, result):
        self.status_label.text = f"Erreur HTTP : {req.resp_status}"
        self.status_label.color = (1, 0.2, 0.2, 1)


if __name__ == "__main__":
    DataMatrixScannerApp().run()
