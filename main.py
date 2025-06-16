#!/usr/bin/env python3
"""
Työsopimuskone - Employment Contract Generator

A PyQt5-based GUI app for creating, previewing, saving, and exporting Finnish employment contracts (työsopimus) as PDFs.
"""

import sys
import warnings
# Suppress macOS secure coding warnings for PyQt5
warnings.filterwarnings("ignore", category=UserWarning, module="PyQt5")

import json # Added json import
import os  # Added os import
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QFileDialog,
    QDateEdit,
    QFormLayout,
    QTextEdit,
    QSplitter,
    QComboBox,
    QSizePolicy,
    QScrollArea,
    QGroupBox,
    QHBoxLayout,  # Added QHBoxLayout import
    QMessageBox   # Added QMessageBox import
)
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

class TyosopimusApp(QWidget):
    """
    Main application window for Työsopimuskone.
    Allows users to input contract details, preview the contract, save/load contracts, and generate PDFs.
    """
    def __init__(self, contracts_file="contracts.json"):
        """
        Initialize the application window and load contracts.
        :param contracts_file: Path to the JSON file for storing contracts.
        """
        super().__init__()
        self.contracts_file = contracts_file
        self.contracts = {}
        self.initUI()
        self.load_contracts()

    def initUI(self):
        """
        Set up the main UI: grouped input fields, preview area, and buttons.
        """
        self.setWindowTitle("Työsopimuskone")
        self.setGeometry(100, 100, 1200, 800) # Increased default size

        # Main layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Top part for selecting previous contracts
        self.contract_selector = QComboBox()
        self.contract_selector.addItem("Uusi sopimus")
        self.contract_selector.currentIndexChanged.connect(self.load_selected_contract)
        main_layout.addWidget(self.contract_selector)

        # Splitter for input and preview
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # --- Input Area (Left Side) ---
        input_area_widget = QWidget()
        input_scroll = QScrollArea() # Make input area scrollable
        input_scroll.setWidgetResizable(True)
        input_scroll.setWidget(input_area_widget)
        splitter.addWidget(input_scroll)

        input_layout = QFormLayout(input_area_widget) # Use QFormLayout for alignment
        input_layout.setSpacing(10) # Add some spacing

        # Highlight style for required fields (label and input)
        required_label_style = "color: #FFA500; font-weight: bold;"  # Orange, bold
        required_input_style = "border: 2px solid #FFA500; background-color: #232323; color: #fff;"  # Orange border, dark bg, white text

        # Contract Date (New Field)
        self.contract_date_label = QLabel("Sopimuspäivämäärä:")
        self.contract_date_label.setStyleSheet(required_label_style)
        self.contract_date_input = QDateEdit(calendarPopup=True)
        self.contract_date_input.setMinimumWidth(300)
        self.contract_date_input.setDate(QDate.currentDate())
        self.contract_date_input.setStyleSheet(required_input_style)
        input_layout.addRow(self.contract_date_label, self.contract_date_input)


        # 1. Työnantaja
        employer_group = QGroupBox()
        employer_group.setTitle("1. Työnantaja")
        employer_layout = QFormLayout(employer_group)
        employer_layout.setLabelAlignment(Qt.AlignLeft)
        employer_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        self.employer_name_input = QLineEdit()
        self.employer_name_input.setMinimumWidth(300)
        self.employer_name_input.setStyleSheet(required_input_style)
        employer_layout.addRow(QLabel("Nimi:").setStyleSheet(required_label_style) or QLabel("Nimi:"), self.employer_name_input)
        self.employer_address_input = QLineEdit()
        self.employer_address_input.setMinimumWidth(300)
        employer_layout.addRow(QLabel("Osoite:"), self.employer_address_input)
        self.employer_id_input = QLineEdit() # Y-tunnus
        self.employer_id_input.setMinimumWidth(300)
        employer_layout.addRow(QLabel("Y-tunnus:"), self.employer_id_input)
        input_layout.addRow(employer_group)

        # 2. Työntekijä
        employee_group = QGroupBox()
        employee_group.setTitle("2. Työntekijä")
        employee_layout = QFormLayout(employee_group)
        employee_layout.setLabelAlignment(Qt.AlignLeft)
        employee_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        self.employee_name_input = QLineEdit()
        self.employee_name_input.setMinimumWidth(300)
        self.employee_name_input.setStyleSheet(required_input_style)
        employee_layout.addRow(QLabel("Nimi:").setStyleSheet(required_label_style) or QLabel("Nimi:"), self.employee_name_input)
        self.employee_address_input = QLineEdit()
        self.employee_address_input.setMinimumWidth(300)
        employee_layout.addRow(QLabel("Osoite:"), self.employee_address_input)
        self.employee_id_input = QLineEdit() # Hetu
        self.employee_id_input.setMinimumWidth(300)
        employee_layout.addRow(QLabel("Henkilötunnus:"), self.employee_id_input)
        input_layout.addRow(employee_group)

        # 3. Työsuhteen alkaminen ja luonne
        employment_details_group = QGroupBox()
        employment_details_group.setTitle("3. Työsuhteen alkaminen ja luonne")
        employment_details_layout = QFormLayout(employment_details_group)
        employment_details_layout.setLabelAlignment(Qt.AlignLeft)
        employment_details_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        self.start_date_input = QDateEdit(calendarPopup=True)
        self.start_date_input.setMinimumWidth(300)
        self.start_date_input.setDate(QDate.currentDate())
        self.start_date_input.setStyleSheet(required_input_style)
        employment_details_layout.addRow(QLabel("Työ alkaa:").setStyleSheet(required_label_style) or QLabel("Työ alkaa:"), self.start_date_input)
        self.contract_type_input = QLineEdit("toistaiseksi voimassa oleva")
        self.contract_type_input.setMinimumWidth(300)
        employment_details_layout.addRow(QLabel("Sopimuksen luonne:"), self.contract_type_input)
        self.probation_period_input = QLineEdit("6 kuukautta")
        self.probation_period_input.setMinimumWidth(300)
        employment_details_layout.addRow(QLabel("Koeaika:"), self.probation_period_input)
        input_layout.addRow(employment_details_group)

        # 4. Työtehtävät ja työntekopaikka
        job_details_group = QGroupBox()
        job_details_group.setTitle("4. Työtehtävät ja työntekopaikka")
        job_details_layout = QFormLayout(job_details_group)
        job_details_layout.setLabelAlignment(Qt.AlignLeft)
        job_details_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        self.job_title_input = QLineEdit()
        self.job_title_input.setMinimumWidth(300)
        job_details_layout.addRow(QLabel("Tehtävänimike:"), self.job_title_input)
        self.main_duties_input = QLineEdit()
        self.main_duties_input.setMinimumWidth(300)
        job_details_layout.addRow(QLabel("Pääasialliset työtehtävät:"), self.main_duties_input)
        self.work_location_input = QLineEdit()
        self.work_location_input.setMinimumWidth(300)
        job_details_layout.addRow(QLabel("Työntekopaikka:"), self.work_location_input)
        input_layout.addRow(job_details_group)

        # 5. Palkkaus
        salary_group = QGroupBox()
        salary_group.setTitle("5. Palkkaus")
        salary_layout = QFormLayout(salary_group)
        salary_layout.setLabelAlignment(Qt.AlignLeft)
        salary_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        self.salary_input = QLineEdit()
        self.salary_input.setMinimumWidth(300)
        self.salary_input.setStyleSheet(required_input_style)
        salary_layout.addRow(QLabel("Palkka (EUR/kk):").setStyleSheet(required_label_style) or QLabel("Palkka (EUR/kk):"), self.salary_input)
        self.salary_payment_date_input = QLineEdit("kuukauden 15. päivä")
        self.salary_payment_date_input.setMinimumWidth(300)
        salary_layout.addRow(QLabel("Palkanmaksukausi ja -päivä:"), self.salary_payment_date_input)
        input_layout.addRow(salary_group)

        # 6. Työaika
        working_hours_group = QGroupBox()
        working_hours_group.setTitle("6. Työaika")
        working_hours_layout = QFormLayout(working_hours_group)
        working_hours_layout.setLabelAlignment(Qt.AlignLeft)
        working_hours_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        self.working_hours_input = QLineEdit("37,5 tuntia / viikko")
        self.working_hours_input.setMinimumWidth(300)
        working_hours_layout.addRow(QLabel("Säännöllinen työaika:"), self.working_hours_input)
        input_layout.addRow(working_hours_group)

        # 7. Vuosiloma
        annual_leave_group = QGroupBox()
        annual_leave_group.setTitle("7. Vuosiloma")
        annual_leave_layout = QFormLayout(annual_leave_group)
        annual_leave_layout.setLabelAlignment(Qt.AlignLeft)
        annual_leave_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        self.annual_leave_input = QLineEdit("vuosilomalain mukaan")
        self.annual_leave_input.setMinimumWidth(300)
        annual_leave_layout.addRow(QLabel("Vuosiloma määräytyy:"), self.annual_leave_input)
        input_layout.addRow(annual_leave_group)

        # 8. Irtisanomisaika
        notice_period_group = QGroupBox()
        notice_period_group.setTitle("8. Irtisanomisaika")
        notice_period_layout = QFormLayout(notice_period_group)
        notice_period_layout.setLabelAlignment(Qt.AlignLeft)
        notice_period_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        self.notice_period_input = QLineEdit("työsopimuslain mukaan")
        self.notice_period_input.setMinimumWidth(300)
        notice_period_layout.addRow(QLabel("Irtisanomisaika määräytyy:"), self.notice_period_input)
        input_layout.addRow(notice_period_group)

        # 9. Sovellettava työehtosopimus
        collective_agreement_group = QGroupBox()
        collective_agreement_group.setTitle("9. Sovellettava työehtosopimus")
        collective_agreement_layout = QFormLayout(collective_agreement_group)
        collective_agreement_layout.setLabelAlignment(Qt.AlignLeft)
        collective_agreement_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        self.collective_agreement_input = QLineEdit("mahdollinen työehtosopimus")
        self.collective_agreement_input.setMinimumWidth(300)
        collective_agreement_layout.addRow(QLabel("Työsuhteessa noudatetaan:"), self.collective_agreement_input)
        input_layout.addRow(collective_agreement_group)

        # 10. Muut ehdot
        other_conditions_group = QGroupBox()
        other_conditions_group.setTitle("10. Muut ehdot")
        other_conditions_layout = QVBoxLayout(other_conditions_group) # QVBoxLayout for QTextEdit
        self.muut_ehdot_input = QTextEdit()
        self.muut_ehdot_input.setPlaceholderText("Kirjoita tähän sopimuksen muut ehdot...")
        self.muut_ehdot_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.muut_ehdot_input.setMinimumHeight(100) # Ensure it has some initial height
        other_conditions_layout.addWidget(self.muut_ehdot_input)
        input_layout.addRow(other_conditions_group)


        # Connect input field changes to update_preview
        for field in [
            self.employer_name_input, self.employer_address_input, self.employer_id_input,
            self.employee_name_input, self.employee_address_input, self.employee_id_input,
            self.contract_type_input, self.probation_period_input, self.job_title_input,
            self.main_duties_input, self.work_location_input, self.salary_input,
            self.salary_payment_date_input, self.working_hours_input, self.annual_leave_input,
            self.notice_period_input, self.collective_agreement_input
        ]:
            field.textChanged.connect(self.update_preview)
        self.start_date_input.dateChanged.connect(self.update_preview)
        self.contract_date_input.dateChanged.connect(self.update_preview) # Added for contract_date
        self.muut_ehdot_input.textChanged.connect(self.update_preview)


        # --- Preview Area (Right Side) ---
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        self.preview_area = QTextEdit()
        self.preview_area.setReadOnly(True)
        preview_layout.addWidget(self.preview_area)
        splitter.addWidget(preview_widget)

        # Set initial sizes for splitter (optional, can be adjusted by user)
        splitter.setSizes([self.width() // 2, self.width() // 2])


        # Buttons
        button_layout = QHBoxLayout() # Horizontal layout for buttons
        self.save_button = QPushButton("Tallenna sopimus")
        self.save_button.clicked.connect(self.save_contract)
        button_layout.addWidget(self.save_button)

        generate_button = QPushButton("Luo PDF")
        generate_button.clicked.connect(self.generate_pdf)
        button_layout.addWidget(generate_button)
        main_layout.addLayout(button_layout) # Add button layout to main layout

        self.update_preview() # Initial preview update

    def get_contract_data(self):
        """
        Collect all contract data from input fields as a dictionary.
        :return: dict of contract details
        """
        return {
            "employer_name": self.employer_name_input.text(),
            "employer_address": self.employer_address_input.text(),
            "employer_id": self.employer_id_input.text(),
            "employee_name": self.employee_name_input.text(),
            "employee_address": self.employee_address_input.text(),
            "employee_id": self.employee_id_input.text(),
            "contract_date": self.contract_date_input.date().toString("dd.MM.yyyy"), # Added contract_date
            "start_date": self.start_date_input.date().toString("dd.MM.yyyy"),
            "contract_type": self.contract_type_input.text(),
            "probation_period": self.probation_period_input.text(),
            "job_title": self.job_title_input.text(),
            "main_duties": self.main_duties_input.text(),
            "work_location": self.work_location_input.text(),
            "salary": self.salary_input.text(),
            "salary_payment_date": self.salary_payment_date_input.text(),
            "working_hours": self.working_hours_input.text(),
            "annual_leave": self.annual_leave_input.text(),
            "notice_period": self.notice_period_input.text(),
            "collective_agreement": self.collective_agreement_input.text(),
            "muut_ehdot": self.muut_ehdot_input.toPlainText(),
        }

    def populate_fields(self, data):
        """
        Populate all input fields from a contract data dictionary.
        :param data: dict of contract details
        """
        self.employer_name_input.setText(data.get("employer_name", ""))
        self.employer_address_input.setText(data.get("employer_address", ""))
        self.employer_id_input.setText(data.get("employer_id", ""))
        self.employee_name_input.setText(data.get("employee_name", ""))
        self.employee_address_input.setText(data.get("employee_address", ""))
        self.employee_id_input.setText(data.get("employee_id", ""))
        
        contract_date_str = data.get("contract_date") # Added for contract_date
        if contract_date_str: # Added for contract_date
            self.contract_date_input.setDate(QDate.fromString(contract_date_str, "dd.MM.yyyy")) # Added for contract_date
        else: # Added for contract_date
            self.contract_date_input.setDate(QDate.currentDate()) # Added for contract_date

        start_date_str = data.get("start_date")
        if start_date_str:
            self.start_date_input.setDate(QDate.fromString(start_date_str, "dd.MM.yyyy"))
        else:
            self.start_date_input.setDate(QDate.currentDate())
        self.contract_type_input.setText(data.get("contract_type", "toistaiseksi voimassa oleva"))
        self.probation_period_input.setText(data.get("probation_period", "6 kuukautta"))
        self.job_title_input.setText(data.get("job_title", ""))
        self.main_duties_input.setText(data.get("main_duties", ""))
        self.work_location_input.setText(data.get("work_location", ""))
        self.salary_input.setText(data.get("salary", ""))
        self.salary_payment_date_input.setText(data.get("salary_payment_date", "kuukauden 15. päivä"))
        self.working_hours_input.setText(data.get("working_hours", "37,5 tuntia / viikko"))
        self.annual_leave_input.setText(data.get("annual_leave", "vuosilomalain mukaan"))
        self.notice_period_input.setText(data.get("notice_period", "työsopimuslain mukaan"))
        self.collective_agreement_input.setText(data.get("collective_agreement", "mahdollinen työehtosopimus"))
        self.muut_ehdot_input.setPlainText(data.get("muut_ehdot", ""))
        self.update_preview()

    def save_contract(self):
        """
        Save the current contract data to a uniquely named JSON file and update the contract selector.
        """
        data = self.get_contract_data()
        contract_name = f"{data['employee_name']}_{data['employer_name']}_tyosopimus.json"
        with open(contract_name, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        self.contracts[contract_name] = data
        self.contract_selector.addItem(contract_name)
        self.contract_selector.setCurrentText(contract_name)
        QMessageBox.information(self, "Tallennettu", f"Sopimus tallennettu nimellä: {contract_name}")

    def load_contracts(self):
        """
        Load all contracts from the contracts file (if it exists) into the selector.
        """
        self.contracts_dir = "contracts"
        self.contracts = {}
        self.contract_files = []
        if not os.path.exists(self.contracts_dir):
            # Silently return if the directory doesn't exist, will be created on save
            return

        for filename in os.listdir(self.contracts_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(self.contracts_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        contract_data = json.load(f)
                        # Use filename without .json as key
                        contract_name = os.path.splitext(filename)[0]
                        self.contracts[contract_name] = contract_data
                        self.contract_files.append(contract_name)
                except FileNotFoundError:
                    # This specific file not found, might be a rare case if dir listing changed
                    # Or if a .json file is not a contract. Silently ignore.
                    pass # Or print a less intrusive log if needed for debugging
                except json.JSONDecodeError:
                    print(f"Error decoding JSON from {filepath}")
                except Exception as e:
                    print(f"Error loading contract {filepath}: {e}")
        
        self.contract_selector.clear()
        self.contract_selector.addItem("Uusi sopimus")
        if self.contract_files:
            self.contract_selector.addItems(sorted(self.contract_files))

    def load_selected_contract(self, index):
        """
        Load the selected contract from the selector into the input fields.
        :param index: Index of the selected contract
        """
        if index == 0:
            # New contract selected
            self.clear_fields()
        else:
            contract_name = self.contract_selector.currentText()
            data = self.contracts.get(contract_name)
            if data:
                self.populate_fields(data)

    def clear_fields(self):
        """
        Clear all input fields and reset to default values.
        """
        for field in [
            self.employer_name_input, self.employer_address_input, self.employer_id_input,
            self.employee_name_input, self.employee_address_input, self.employee_id_input,
            self.contract_type_input, self.probation_period_input, self.job_title_input,
            self.main_duties_input, self.work_location_input, self.salary_input,
            self.salary_payment_date_input, self.working_hours_input, self.annual_leave_input,
            self.notice_period_input, self.collective_agreement_input, self.muut_ehdot_input
        ]:
            field.clear()
        self.contract_date_input.setDate(QDate.currentDate()) # Added for contract_date
        self.start_date_input.setDate(QDate.currentDate())
        self.contract_type_input.setText("toistaiseksi voimassa oleva")
        self.probation_period_input.setText("6 kuukautta")
        self.salary_payment_date_input.setText("kuukauden 15. päivä")
        self.working_hours_input.setText("37,5 tuntia / viikko")
        self.annual_leave_input.setText("vuosilomalain mukaan")
        self.notice_period_input.setText("työsopimuslain mukaan")
        self.collective_agreement_input.setText("mahdollinen työehtosopimus")
        self.update_preview()

    def update_preview(self):
        """
        Update the live HTML preview area with the current contract data.
        """
        data = self.get_contract_data()
        muut_ehdot_html = data['muut_ehdot'].replace("\\n", "<br />")

        html_content = f'''
        <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
        <html><head><meta name="qrichtext" content="1" /><style type="text/css">
        p, li {{ white-space: pre-wrap; }}
        body {{ font-family: 'Helvetica', 'Arial', 'sans-serif'; font-size: 12pt; }}
        h1 {{ font-size: 16pt; font-weight: bold; margin-bottom: 10px; }}
        h2 {{ font-size: 14pt; font-weight: bold; margin-top: 15px; margin-bottom: 5px; }}
        h3 {{ font-size: 12pt; font-weight: bold; margin-top: 10px; margin-bottom: 5px; }}
        hr {{ margin-top: 10px; margin-bottom: 10px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        td {{ padding: 5px; vertical-align: top; }}
        .contract-date {{ text-align: right; font-size: 10pt; margin-bottom: 20px; }}
        </style></head><body>
        <h2 style="text-align: center;">TYÖSOPIMUS</h2>
        <p class="contract-date"><b>Sopimuspäivämäärä:</b> {data['contract_date']}</p>
        <hr />

        <h3>1. Työnantaja</h3>
        <p><b>Nimi:</b> {data['employer_name']}</p>
        <p><b>Osoite:</b> {data['employer_address']}</p>
        <p><b>Y-tunnus:</b> {data['employer_id']}</p>

        <h3>2. Työntekijä</h3>
        <p><b>Nimi:</b> {data['employee_name']}</p>
        <p><b>Osoite:</b> {data['employee_address']}</p>
        <p><b>Henkilötunnus:</b> {data['employee_id']}</p>

        <h3>3. Työsuhteen alkaminen ja luonne</h3>
        <p><b>Työ alkaa:</b> {data['start_date']}</p>
        <p><b>Sopimuksen luonne:</b> {data['contract_type']}</p>
        <p><b>Koeaika:</b> {data['probation_period']}</p>

        <h3>4. Työtehtävät ja työntekopaikka</h3>
        <p><b>Tehtävänimike:</b> {data['job_title']}</p>
        <p><b>Pääasialliset työtehtävät:</b> {data['main_duties']}</p>
        <p><b>Työntekopaikka:</b> {data['work_location']}</p>

        <h3>5. Palkkaus</h3>
        <p><b>Palkka:</b> {data['salary']} euroa kuukaudessa</p>
        <p><b>Palkanmaksukausi ja -päivä:</b> {data['salary_payment_date']}</p>

        <h3>6. Työaika</h3>
        <p><b>Säännöllinen työaika:</b> {data['working_hours']}</p>

        <h3>7. Vuosiloma</h3>
        <p><b>Vuosiloma määräytyy:</b> {data['annual_leave']}</p>

        <h3>8. Irtisanomisaika</h3>
        <p><b>Irtisanomisaika määräytyy:</b> {data['notice_period']}</p>

        <h3>9. Sovellettava työehtosopimus</h3>
        <p><b>Työsuhteessa noudatetaan:</b> {data['collective_agreement']}</p>

        <h3>10. Muut ehdot</h3>
        <p>{muut_ehdot_html}</p>
        <br><br>
        <p><b>Allekirjoitukset</b></p>
        <br><br><br>
        <table border="0" width="100%">
            <tr>
                <td width="50%">_________________________</td>
                <td width="50%">_________________________</td>
            </tr>
            <tr>
                <td>{data['employer_name']}</td>
                <td>{data['employee_name']}</td>
            </tr>
            <tr>
                <td>(Työnantaja)</td>
                <td>(Työntekijä)</td>
            </tr>
        </table>
        </body></html>
        '''
        self.preview_area.setHtml(html_content)

    def generate_pdf(self):
        """Generates a PDF document from the current contract data."""
        data = self.get_contract_data()
        filename, _ = QFileDialog.getSaveFileName(self, "Tallenna PDF", 
                                                  f"{data.get('employee_name', 'tyhja')}_{data.get('employer_name', 'tyhja')}_tyosopimus.pdf",
                                                  "PDF Files (*.pdf)")
        if not filename:
            return

        doc = SimpleDocTemplate(filename, pagesize=letter,
                                rightMargin=inch, leftMargin=inch,
                                topMargin=inch, bottomMargin=inch)
        styles = getSampleStyleSheet()

        # Custom styles with unique names to avoid KeyError and for improved appearance
        styles.add(ParagraphStyle(name='CustomHeading1', parent=styles['Heading1'], fontName='Times-Bold', fontSize=22, alignment=TA_CENTER, spaceAfter=24, spaceBefore=12))
        styles.add(ParagraphStyle(name='CustomHeading2', parent=styles['Heading2'], fontName='Times-Bold', fontSize=16, spaceBefore=16, spaceAfter=10))
        styles.add(ParagraphStyle(name='CustomHeading3', parent=styles['Heading3'], fontName='Times-Bold', fontSize=13, spaceBefore=12, spaceAfter=6))
        styles.add(ParagraphStyle(name='BodyTextBold', parent=styles['Normal'], fontName='Helvetica-Bold'))
        styles.add(ParagraphStyle(name='BodyTextSpaced', parent=styles['Normal'], spaceBefore=6, spaceAfter=6))

        story = []

        story.append(Paragraph("TYÖSOPIMUS", styles['CustomHeading1']))
        story.append(Spacer(1, 0.1*inch))
        story.append(Paragraph(f"Sopimuspäivämäärä: {data.get('contract_date', QDate.currentDate().toString('dd.MM.yyyy'))}", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))

        sections = [
            ("1. Työnantaja", [
                (f"<b>Nimi:</b> {data.get('employer_name', '')}", styles['Normal']),
                (f"<b>Osoite:</b> {data.get('employer_address', '')}", styles['Normal']),
                (f"<b>Y-tunnus:</b> {data.get('employer_id', '')}", styles['Normal'])
            ]),
            ("2. Työntekijä", [
                (f"<b>Nimi:</b> {data.get('employee_name', '')}", styles['Normal']),
                (f"<b>Osoite:</b> {data.get('employee_address', '')}", styles['Normal']),
                (f"<b>Henkilötunnus:</b> {data.get('employee_id', '')}", styles['Normal'])
            ]),
            ("3. Työsuhteen alkaminen ja luonne", [
                (f"<b>Työ alkaa:</b> {data.get('start_date', '')}", styles['Normal']),
                (f"<b>Sopimuksen luonne:</b> {data.get('contract_type', '')}", styles['Normal']),
                (f"<b>Koeaika:</b> {data.get('probation_period', '')}", styles['Normal'])
            ]),
            ("4. Työtehtävät ja työntekopaikka", [
                (f"<b>Tehtävänimike:</b> {data.get('job_title', '')}", styles['Normal']),
                (Paragraph(f"<b>Pääasialliset työtehtävät:</b> {data.get('main_duties', '').replace(chr(10), '<br/>')}", styles['Normal'])),
                (f"<b>Työntekopaikka:</b> {data.get('work_location', '')}", styles['Normal'])
            ]),
            ("5. Palkkaus", [
                (f"<b>Palkka:</b> {data.get('salary', '')} euroa kuukaudessa", styles['Normal']),
                (f"<b>Palkanmaksukausi ja -päivä:</b> {data.get('salary_payment_date', '')}", styles['Normal'])
            ]),
            ("6. Työaika", [
                (f"<b>Säännöllinen työaika:</b> {data.get('working_hours', '')}", styles['Normal'])
            ]),
            ("7. Vuosiloma", [
                (f"<b>Vuosiloma määräytyy:</b> {data.get('annual_leave', '')}", styles['Normal'])
            ]),
            ("8. Irtisanomisaika", [
                (f"<b>Irtisanomisaika määräytyy:</b> {data.get('notice_period', '')}", styles['Normal'])
            ]),
            ("9. Sovellettava työehtosopimus", [
                (f"<b>Työsuhteessa noudatetaan:</b> {data.get('collective_agreement', '')}", styles['Normal'])
            ]),
            ("10. Muut ehdot", [
                (Paragraph(data.get('muut_ehdot', '').replace(chr(10), '<br/>'), styles['Normal']))
            ])
        ]

        for title, items in sections:
            story.append(Paragraph(title, styles['CustomHeading2']))
            for item in items:
                if isinstance(item, tuple):
                    story.append(Paragraph(item[0], item[1]))
                else:
                    story.append(item)
                story.append(Spacer(1, 0.1*inch))
            story.append(Spacer(1, 0.1*inch))

        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph("Allekirjoitukset", styles['CustomHeading2']))
        story.append(Spacer(1, 0.5*inch))

        # Signatures table
        signature_data = [
            [Paragraph("_________________________", styles['Normal']), Paragraph("_________________________", styles['Normal'])],
            [Paragraph(data.get('employer_name', 'Työnantaja'), styles['Normal']), Paragraph(data.get('employee_name', 'Työntekijä'), styles['Normal'])],
            [Paragraph("(Työnantaja)", styles['Normal']), Paragraph("(Työntekijä)", styles['Normal'])]
        ]
        table = Table(signature_data, colWidths=[3*inch, 3*inch])
        table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'TOP')
        ]))
        story.append(table)

        try:
            doc.build(story)
            QMessageBox.information(self, "PDF Luotu", f"PDF luotu: {filename}")
            print(f"PDF luotu: {filename}") # Keep for test verification
        except Exception as e:
            QMessageBox.critical(self, "Virhe", f"PDF-tiedoston luonti epäonnistui: {e}")
            print(f"PDF generation failed: {e}") # Keep for test verification

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = TyosopimusApp()
    ex.show()
    sys.exit(app.exec_())
