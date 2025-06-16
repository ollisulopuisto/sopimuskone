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
    QHBoxLayout, # Added QHBoxLayout
    QFileDialog,
    QDateEdit,
    QFormLayout,
    QTextEdit,
    QSplitter,
    QComboBox,
    QSizePolicy,
    QScrollArea,
    QGroupBox,
    QCheckBox,  # Added QCheckBox
    QMessageBox, QRadioButton, QButtonGroup # Moved QMessageBox import here
)
from PyQt5.QtCore import Qt, QDate, QSize # Added QSize
from PyQt5.QtGui import QPalette, QColor, QFont # Added QFont

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY # Added TA_RIGHT, TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch

# Default probation period
DEFAULT_PROBATION_PERIOD = "6 kuukautta"
# Default salary payment date
DEFAULT_SALARY_PAYMENT_DATE = "kuukauden 15. päivä"
# Default working hours
DEFAULT_WORKING_HOURS = "37,5 tuntia / viikko"
# Default annual leave
DEFAULT_ANNUAL_LEAVE = "vuosilomalain mukaan"
# Default notice period
DEFAULT_NOTICE_PERIOD = "työsopimuslain mukaan"
# Default collective agreement
DEFAULT_COLLECTIVE_AGREEMENT = "mahdollinen työehtosopimus"


class TyosopimusApp(QWidget):
    def __init__(self, contracts_file=None): # contracts_file is not used by save/load
        super().__init__()
        self.contracts = {}  # Stores loaded contract data
        
        if os.environ.get("TESTING") == "True":
            # During testing, use a temporary directory within the current working directory
            self.contracts_dir = os.path.join(os.getcwd(), "test_contracts_temp")
        else:
            self.contracts_dir = os.path.expanduser("~/Documents/sopimukset") # Primary directory
            
        self.initUI()
        self.load_contracts() # Load existing contracts on startup

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
        self.employment_details_layout = QFormLayout(employment_details_group)
        self.employment_details_layout.setLabelAlignment(Qt.AlignLeft)
        self.employment_details_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        
        self.start_date_input = QDateEdit(calendarPopup=True)
        self.start_date_input.setMinimumWidth(300)
        self.start_date_input.setDate(QDate.currentDate())
        self.start_date_input.setStyleSheet(required_input_style)
        self.employment_details_layout.addRow(QLabel("Työ alkaa:").setStyleSheet(required_label_style) or QLabel("Työ alkaa:"), self.start_date_input)
        
        # Contract type radio buttons (replace checkboxes)
        contract_type_layout = QHBoxLayout()
        self.permanent_contract_radio = QRadioButton("Toistaiseksi voimassa oleva työsopimus")
        self.temporary_contract_radio = QRadioButton("Määräaikainen työsopimus")
        self.permanent_contract_radio.setChecked(True)  # Default to permanent
        self.contract_type_group = QButtonGroup()
        self.contract_type_group.addButton(self.permanent_contract_radio)
        self.contract_type_group.addButton(self.temporary_contract_radio)
        contract_type_layout.addWidget(self.permanent_contract_radio)
        contract_type_layout.addWidget(self.temporary_contract_radio)
        self.employment_details_layout.addRow(QLabel("Sopimuksen luonne:"), contract_type_layout)
        
        # Temporary contract fields (initially hidden)
        self.temp_contract_reason_input = QLineEdit()
        self.temp_contract_reason_input.setMinimumWidth(300)
        self.temp_contract_reason_input.setPlaceholderText("Määräaikaisuuden peruste")
        self.temp_contract_reason_label = QLabel("Määräaikaisuuden peruste:")
        self.employment_details_layout.addRow(self.temp_contract_reason_label, self.temp_contract_reason_input)
        
        self.end_date_input = QDateEdit(calendarPopup=True)
        self.end_date_input.setMinimumWidth(300)
        self.end_date_input.setDate(QDate.currentDate().addMonths(12))  # Default 1 year
        self.end_date_label = QLabel("Määräaikaisuus päättyy:")
        self.employment_details_layout.addRow(self.end_date_label, self.end_date_input)
        
        # Probation period (hidden for temporary contracts)
        self.probation_period_input = QLineEdit("6 kuukautta")
        self.probation_period_input.setMinimumWidth(300)
        self.probation_period_label = QLabel("Koeaika:")
        self.employment_details_layout.addRow(self.probation_period_label, self.probation_period_input)
        
        # Initially hide temporary contract fields
        self.temp_contract_reason_label.setVisible(False)
        self.temp_contract_reason_input.setVisible(False)
        self.end_date_label.setVisible(False)
        self.end_date_input.setVisible(False)
        
        # Connect radio buttons to toggle function
        self.permanent_contract_radio.toggled.connect(self.toggle_contract_type)
        self.temporary_contract_radio.toggled.connect(self.toggle_contract_type)
        
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
        salary_layout.addRow(QLabel("Työstä maksettava palkka tai muu vastike:").setStyleSheet(required_label_style) or QLabel("Työstä maksettava palkka tai muu vastike:"), self.salary_input)
        
        self.salary_basis_input = QLineEdit()
        self.salary_basis_input.setMinimumWidth(300)
        self.salary_basis_input.setPlaceholderText("esim. kuukausipalkka, tuntipalkka, suoritusperuste")
        salary_layout.addRow(QLabel("Palkan määräytymisen peruste:"), self.salary_basis_input)
        
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
        self.working_hours_input.setPlaceholderText("esim. säännöllinen työaika, max 15 h/vko")
        working_hours_layout.addRow(QLabel("Työaika:"), self.working_hours_input)
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

        # 9. Sovellettava työehtosopimus (optional)
        collective_agreement_group = QGroupBox()
        collective_agreement_group.setTitle("9. Sovellettava työehtosopimus")
        collective_agreement_layout = QFormLayout(collective_agreement_group)
        collective_agreement_layout.setLabelAlignment(Qt.AlignLeft)
        collective_agreement_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        
        # Add checkbox to make this section optional
        self.collective_agreement_checkbox = QCheckBox("Sisällytä työehtosopimus sopimukseen")
        self.collective_agreement_checkbox.setChecked(False)  # Optional by default
        collective_agreement_layout.addRow(self.collective_agreement_checkbox)
        
        self.collective_agreement_input = QLineEdit("mahdollinen työehtosopimus")
        self.collective_agreement_input.setMinimumWidth(300)
        self.collective_agreement_label = QLabel("Työsuhteessa noudatetaan:")
        collective_agreement_layout.addRow(self.collective_agreement_label, self.collective_agreement_input)
        
        # Initially hide the input field since checkbox is unchecked
        self.collective_agreement_label.setVisible(False)
        self.collective_agreement_input.setVisible(False)
        
        # Connect checkbox to toggle visibility
        self.collective_agreement_checkbox.toggled.connect(self.toggle_collective_agreement)
        
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
            self.probation_period_input, self.job_title_input,
            self.main_duties_input, self.work_location_input, self.salary_input,
            self.salary_basis_input, self.temp_contract_reason_input,
            self.salary_payment_date_input, self.working_hours_input, self.annual_leave_input,
            self.notice_period_input, self.collective_agreement_input
        ]:
            field.textChanged.connect(self.update_preview)
        self.start_date_input.dateChanged.connect(self.update_preview)
        self.end_date_input.dateChanged.connect(self.update_preview)
        self.contract_date_input.dateChanged.connect(self.update_preview) # Added for contract_date
        self.permanent_contract_radio.toggled.connect(self.update_preview)
        self.temporary_contract_radio.toggled.connect(self.update_preview)
        self.collective_agreement_checkbox.toggled.connect(self.update_preview)
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
        # Determine contract type
        if self.temporary_contract_radio.isChecked():
            contract_type = "määräaikainen"
        else:
            contract_type = "toistaiseksi voimassa oleva"
        return {
            "employer_name": self.employer_name_input.text(),
            "employer_address": self.employer_address_input.text(),
            "employer_id": self.employer_id_input.text(),
            "employee_name": self.employee_name_input.text(),
            "employee_address": self.employee_address_input.text(),
            "employee_id": self.employee_id_input.text(),
            "contract_date": self.contract_date_input.date().toString("dd.MM.yyyy"),
            "start_date": self.start_date_input.date().toString("dd.MM.yyyy"),
            "contract_type": contract_type,
            "is_temporary": self.temporary_contract_radio.isChecked(),
            "temp_contract_reason": self.temp_contract_reason_input.text() if self.temporary_contract_radio.isChecked() else "",
            "end_date": self.end_date_input.date().toString("dd.MM.yyyy") if self.temporary_contract_radio.isChecked() else "",
            "probation_period": self.probation_period_input.text(),
            "job_title": self.job_title_input.text(),
            "main_duties": self.main_duties_input.text(),
            "work_location": self.work_location_input.text(),
            "salary": self.salary_input.text(),
            "salary_basis": self.salary_basis_input.text(),
            "salary_payment_date": self.salary_payment_date_input.text(),
            "working_hours": self.working_hours_input.text(),
            "annual_leave": self.annual_leave_input.text(),
            "notice_period": self.notice_period_input.text(),
            "collective_agreement": self.collective_agreement_input.text(),
            "has_collective_agreement": self.collective_agreement_checkbox.isChecked(),
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
        
        # Handle contract type
        is_temporary = data.get("is_temporary", False)
        if is_temporary:
            self.temporary_contract_radio.setChecked(True)
            self.temp_contract_reason_input.setText(data.get("temp_contract_reason", ""))
            end_date_str = data.get("end_date")
            if end_date_str:
                self.end_date_input.setDate(QDate.fromString(end_date_str, "dd.MM.yyyy"))
        else:
            self.permanent_contract_radio.setChecked(True)
        self.toggle_contract_type()
        
        self.probation_period_input.setText(data.get("probation_period", "6 kuukautta"))
        self.job_title_input.setText(data.get("job_title", ""))
        self.main_duties_input.setText(data.get("main_duties", ""))
        self.work_location_input.setText(data.get("work_location", ""))
        self.salary_input.setText(data.get("salary", ""))
        self.salary_basis_input.setText(data.get("salary_basis", ""))
        self.salary_payment_date_input.setText(data.get("salary_payment_date", "kuukauden 15. päivä"))
        self.working_hours_input.setText(data.get("working_hours", "37,5 tuntia / viikko"))
        self.annual_leave_input.setText(data.get("annual_leave", "vuosilomalain mukaan"))
        self.notice_period_input.setText(data.get("notice_period", "työsopimuslain mukaan"))
        self.collective_agreement_input.setText(data.get("collective_agreement", "mahdollinen työehtosopimus"))
        self.collective_agreement_checkbox.setChecked(data.get("has_collective_agreement", False))
        self.toggle_collective_agreement()  # Update visibility based on checkbox state
        self.muut_ehdot_input.setPlainText(data.get("muut_ehdot", ""))
        self.update_preview()

    def save_contract(self):
        """
        Save the current contract data to a timestamped JSON file in the contracts directory.
        """
        from datetime import datetime
        
        data = self.get_contract_data()
        
        # Add timestamp information to contract data
        timestamp = datetime.now()
        data['created_at'] = timestamp.isoformat()
        data['display_name'] = f"{data['employee_name']} - {data['employer_name']}"
        
        # Create filename with timestamp to avoid overwrites
        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
        safe_employee = "".join(c for c in data['employee_name'] if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_employer = "".join(c for c in data['employer_name'] if c.isalnum() or c in (' ', '-', '_')).strip()
        contract_filename = f"{safe_employee}_{safe_employer}_{timestamp_str}.json"
        
        # Ensure contracts directory self.contracts_dir exists
        if not os.path.exists(self.contracts_dir):
            os.makedirs(self.contracts_dir, exist_ok=True) # Use self.contracts_dir and add exist_ok=True
        
        # Check if file already exists and confirm overwrite
        contract_path = os.path.join(self.contracts_dir, contract_filename) # Use self.contracts_dir
        if os.path.exists(contract_path):
            # from PyQt5.QtWidgets import QMessageBox # No longer needed here
            reply = QMessageBox.question(self, 'Tiedosto olemassa', 
                                       f'Tiedosto {contract_filename} on jo olemassa. Haluatko korvata sen?',
                                       QMessageBox.Yes | QMessageBox.No, 
                                       QMessageBox.No)
            if reply == QMessageBox.No:
                return
        
        # Save to contracts directory
        with open(contract_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
        # Use filename without .json as the key for consistency with load_contracts
        contract_name = os.path.splitext(contract_filename)[0]
        self.contracts[contract_name] = data
        
        # Reload contracts to update the display with proper formatting
        self.load_contracts()
        
        # Find and select the newly saved contract
        for i in range(self.contract_selector.count()):
            item_contract_name = self.contract_selector.itemData(i)
            if item_contract_name == contract_name:
                self.contract_selector.setCurrentIndex(i)
                break
        
        QMessageBox.information(self, "Tallennettu", f"Sopimus tallennettu nimellä: {contract_filename}")

    def load_contracts(self):
        """
        Load contracts from JSON files in specified directories.
        Prioritizes the primary contracts directory, then falls back to others for compatibility.
        During testing (TESTING=True env var), only the test-specific directory is used.
        """
        self.contracts = {}
        self.contract_files = []  # Will contain tuples of (contract_name, display_name)

        if os.environ.get("TESTING") == "True":
            # During testing, only use the specific test contracts directory
            search_dirs = [self.contracts_dir]
        else:
            # Define directories to search for contract JSON files in normal operation
            search_dirs = [
                self.contracts_dir,  # Primary contracts directory (e.g., ~/Documents/sopimukset)
                "contracts",         # Local contracts directory (for backward compatibility)
                "."                  # Current working directory (for backward compatibility)
            ]
        
        for directory in search_dirs:
            if not os.path.exists(directory):
                continue
                
            for filename in os.listdir(directory):
                if filename.endswith(".json"):
                    filepath = os.path.join(directory, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            contract_data = json.load(f)
                            
                            # Check if this looks like a contract file by checking for key fields
                            if self._is_contract_file(contract_data):
                                # Use filename without .json as key, avoid duplicates
                                contract_name = os.path.splitext(filename)[0]
                                if contract_name not in self.contracts:
                                    self.contracts[contract_name] = contract_data
                                    # Create a display name with date if available
                                    display_name = self._create_display_name(contract_data, contract_name)
                                    self.contract_files.append((contract_name, display_name))
                    except FileNotFoundError:
                        # This specific file not found, might be a rare case if dir listing changed
                        pass
                    except json.JSONDecodeError:
                        # Not a valid JSON file, skip silently
                        pass
                    except (OSError, IOError, UnicodeDecodeError):
                        # Other errors (file access, encoding), skip silently to avoid disrupting the app
                        pass
        
        self.contract_selector.clear()
        self.contract_selector.addItem("Uusi sopimus")
        if self.contract_files:
            # Sort by date (newest first), then by name
            sorted_contracts = sorted(self.contract_files, key=lambda x: self._get_sort_key(x[0]), reverse=True)
            for contract_name, display_name in sorted_contracts:
                self.contract_selector.addItem(display_name)
                # Store the mapping between display name and contract name
                self.contract_selector.setItemData(self.contract_selector.count()-1, contract_name)
    
    def _create_display_name(self, contract_data, contract_name):
        """Create a formatted display name for the contract selector."""
        from datetime import datetime
        
        # Try to get display name from contract data first
        if 'display_name' in contract_data:
            display_base = contract_data['display_name']
        else:
            # Fallback to employee and employer names
            employee = contract_data.get('employee_name', 'Tuntematon')
            employer = contract_data.get('employer_name', 'Tuntematon')
            display_base = f"{employee} - {employer}"
        
        # Try to extract date from created_at or filename
        date_str = ""
        if 'created_at' in contract_data:
            try:
                created_at = datetime.fromisoformat(contract_data['created_at'])
                date_str = created_at.strftime(" (%d.%m.%Y)")
            except (ValueError, TypeError):
                pass
        
        # If no created_at, try to parse date from filename
        if not date_str:
            try:
                # Look for timestamp pattern in filename: YYYYMMDD_HHMMSS
                import re
                match = re.search(r'(\d{8})_(\d{6})', contract_name)
                if match:
                    date_part = match.group(1)
                    parsed_date = datetime.strptime(date_part, "%Y%m%d")
                    date_str = parsed_date.strftime(" (%d.%m.%Y)")
            except (ValueError, TypeError):
                pass
        
        return display_base + date_str
    
    def _get_sort_key(self, contract_name):
        """Get sort key for contract (timestamp if available, otherwise filename)."""
        from datetime import datetime
        
        contract_data = self.contracts.get(contract_name, {})
        
        # Try to get timestamp from created_at
        if 'created_at' in contract_data:
            try:
                return datetime.fromisoformat(contract_data['created_at'])
            except (ValueError, TypeError):
                pass
        
        # Try to extract timestamp from filename
        try:
            import re
            match = re.search(r'(\d{8})_(\d{6})', contract_name)
            if match:
                datetime_str = match.group(1) + match.group(2)
                return datetime.strptime(datetime_str, "%Y%m%d%H%M%S")
        except (ValueError, TypeError):
            pass
        
        # Fallback to filename as string (ensure consistent type)
        return datetime(1900, 1, 1)  # Use very old date for fallback to maintain datetime type
    
    def _is_contract_file(self, data):
        """
        Check if the JSON data represents a contract file by looking for key fields.
        :param data: Dictionary containing the JSON data
        :return: True if it looks like a contract file, False otherwise
        """
        # Check for some key contract fields to determine if this is a contract JSON
        key_fields = ['employee_name', 'employer_name', 'contract_date']
        return isinstance(data, dict) and any(field in data for field in key_fields)

    def load_selected_contract(self, index):
        """
        Load the selected contract from the selector into the input fields.
        :param index: Index of the selected contract
        """
        if index == 0:
            # New contract selected
            self.clear_fields()
        else:
            # Get the actual contract name from item data (not the display text)
            contract_name = self.contract_selector.itemData(index)
            if contract_name and contract_name in self.contracts:
                data = self.contracts[contract_name]
                self.populate_fields(data)
            else:
                # Fallback to using display text (for backward compatibility)
                display_text = self.contract_selector.currentText()
                # Try to find contract by matching display name parts
                for name, contract_data in self.contracts.items():
                    if (contract_data.get('employee_name', '') in display_text and 
                        contract_data.get('employer_name', '') in display_text):
                        self.populate_fields(contract_data)
                        break

    def clear_fields(self):
        """
        Clear all input fields and reset to default values.
        """
        for field in [
            self.employer_name_input, self.employer_address_input, self.employer_id_input,
            self.employee_name_input, self.employee_address_input, self.employee_id_input,
            self.probation_period_input, self.job_title_input,
            self.main_duties_input, self.work_location_input, self.salary_input,
            self.salary_basis_input, self.temp_contract_reason_input,
            self.salary_payment_date_input, self.working_hours_input, self.annual_leave_input,
            self.notice_period_input, self.collective_agreement_input, self.muut_ehdot_input
        ]:
            field.clear()
        self.contract_date_input.setDate(QDate.currentDate()) # Added for contract_date
        self.start_date_input.setDate(QDate.currentDate())
        self.end_date_input.setDate(QDate.currentDate().addMonths(12))
        self.permanent_contract_radio.setChecked(True)
        self.toggle_contract_type()
        self.probation_period_input.setText("6 kuukautta")
        self.salary_payment_date_input.setText("kuukauden 15. päivä")
        self.working_hours_input.setText("37,5 tuntia / viikko")
        self.annual_leave_input.setText("vuosilomalain mukaan")
        self.notice_period_input.setText("työsopimuslain mukaan")
        self.collective_agreement_input.setText("mahdollinen työehtosopimus")
        self.collective_agreement_checkbox.setChecked(False)
        self.toggle_collective_agreement()  # Hide collective agreement field
        self.update_preview()

    def update_preview(self):
        """
        Update the live HTML preview area with the current contract data.
        """
        data = self.get_contract_data()
        muut_ehdot_html = data['muut_ehdot'].replace("\\n", "<br />")

        # Build temporary contract section conditionally
        temp_contract_section = ""
        probation_section = ""
        
        if data['is_temporary']:
            temp_contract_section = f'''
        <p><b>Määräaikaisuuden peruste:</b> {data['temp_contract_reason']}</p>
        <p><b>Määräaikaisuus päättyy:</b> {data['end_date']}</p>'''
        else:
            # Only show probation period for permanent contracts
            probation_section = f'''
        <p><b>Koeaika:</b> {data['probation_period']}</p>'''

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
        <p><b>Sopimuksen luonne:</b> {data['contract_type']}</p>{temp_contract_section}{probation_section}

        <h3>4. Työtehtävät ja työntekopaikka</h3>
        <p><b>Tehtävänimike:</b> {data['job_title']}</p>
        <p><b>Pääasialliset työtehtävät:</b> {data['main_duties']}</p>
        <p><b>Työntekopaikka:</b> {data['work_location']}</p>

        <h3>5. Palkkaus</h3>
        <p><b>Työstä maksettava palkka tai muu vastike:</b> {data['salary']}</p>
        <p><b>Palkan määräytymisen peruste:</b> {data['salary_basis']}</p>
        <p><b>Palkanmaksukausi ja -päivä:</b> {data['salary_payment_date']}</p>

        <h3>6. Työaika</h3>
        <p><b>Työaika:</b> {data['working_hours']}</p>

        <h3>7. Vuosiloma</h3>
        <p><b>Vuosiloma määräytyy:</b> {data['annual_leave']}</p>

        <h3>8. Irtisanomisaika</h3>
        <p><b>Irtisanomisaika määräytyy:</b> {data['notice_period']}</p>

        {"<h3>9. Sovellettava työehtosopimus</h3><p><b>Työsuhteessa noudatetaan:</b> " + data['collective_agreement'] + "</p>" if data.get('has_collective_agreement', False) else ""}

        <h3>{"10" if data.get('has_collective_agreement', False) else "9"}. Muut ehdot</h3>
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

        # Build sections dynamically based on contract type
        employment_section = [
            (f"<b>Työ alkaa:</b> {data.get('start_date', '')}", styles['Normal']),
            (f"<b>Sopimuksen luonne:</b> {data.get('contract_type', '')}", styles['Normal'])
        ]
        
        # Add temporary contract specific fields if applicable
        if data.get('is_temporary', False):
            employment_section.extend([
                (f"<b>Määräaikaisuuden peruste:</b> {data.get('temp_contract_reason', '')}", styles['Normal']),
                (f"<b>Määräaikaisuus päättyy:</b> {data.get('end_date', '')}", styles['Normal'])
            ])
        else:
            # Only add probation period for permanent contracts
            employment_section.append((f"<b>Koeaika:</b> {data.get('probation_period', '')}", styles['Normal']))

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
            ("3. Työsuhteen alkaminen ja luonne", employment_section),
            ("4. Työtehtävät ja työntekopaikka", [
                (f"<b>Tehtävänimike:</b> {data.get('job_title', '')}", styles['Normal']),
                (Paragraph(f"<b>Pääasialliset työtehtävät:</b> {data.get('main_duties', '').replace(chr(10), '<br/>')}", styles['Normal'])),
                (f"<b>Työntekopaikka:</b> {data.get('work_location', '')}", styles['Normal'])
            ]),
            ("5. Palkkaus", [
                (f"<b>Työstä maksettava palkka tai muu vastike:</b> {data.get('salary', '')}", styles['Normal']),
                (f"<b>Palkan määräytymisen peruste:</b> {data.get('salary_basis', '')}", styles['Normal']),
                (f"<b>Palkanmaksukausi ja -päivä:</b> {data.get('salary_payment_date', '')}", styles['Normal'])
            ]),
            ("6. Työaika", [
                (f"<b>Työaika:</b> {data.get('working_hours', '')}", styles['Normal'])
            ]),
            ("7. Vuosiloma", [
                (f"<b>Vuosiloma määräytyy:</b> {data.get('annual_leave', '')}", styles['Normal'])
            ]),
            ("8. Irtisanomisaika", [
                (f"<b>Irtisanomisaika määräytyy:</b> {data.get('notice_period', '')}", styles['Normal'])
            ]),
        ]
        
        # Add collective agreement section only if checkbox is checked
        if data.get('has_collective_agreement', False):
            sections.append(("9. Sovellettava työehtosopimus", [
                (f"<b>Työsuhteessa noudatetaan:</b> {data.get('collective_agreement', '')}", styles['Normal'])
            ]))
            muut_ehdot_number = "10"
        else:
            muut_ehdot_number = "9"
        
        # Add the final section with correct numbering
        sections.append((f"{muut_ehdot_number}. Muut ehdot", [
            (Paragraph(data.get('muut_ehdot', '').replace(chr(10), '<br/>'), styles['Normal']))
        ]))

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

    def toggle_contract_type(self):
        """Toggle visibility of temporary contract fields based on contract type selection."""
        is_temp = self.temporary_contract_radio.isChecked()
        # Set both label and input visibility explicitly for robust testability
        self.temp_contract_reason_label.setVisible(is_temp)
        self.temp_contract_reason_input.setVisible(is_temp)
        self.end_date_label.setVisible(is_temp)
        self.end_date_input.setVisible(is_temp)
        self.probation_period_label.setVisible(not is_temp)
        self.probation_period_input.setVisible(not is_temp)
        # If neither is checked, default to permanent
        if not self.temporary_contract_radio.isChecked() and not self.permanent_contract_radio.isChecked():
            self.permanent_contract_radio.setChecked(True)
        self.update_preview()

    def _set_form_row_visible(self, label_widget, visible):
        """Set visibility of a form row by finding the label widget and its corresponding field."""
        layout = self.employment_details_layout
        for i in range(layout.rowCount()):
            label_item = layout.itemAt(i, layout.LabelRole)
            field_item = layout.itemAt(i, layout.FieldRole)
            
            if label_item and label_item.widget() == label_widget:
                # Found the row, set visibility for both label and field
                if label_item.widget():
                    label_item.widget().setVisible(visible)
                if field_item and field_item.widget():
                    field_item.widget().setVisible(visible)
                break
        
        self.update_preview()

    def toggle_collective_agreement(self):
        """Toggle visibility of collective agreement input field based on checkbox state."""
        is_checked = self.collective_agreement_checkbox.isChecked()
        self.collective_agreement_label.setVisible(is_checked)
        self.collective_agreement_input.setVisible(is_checked)
        if is_checked:
            self.collective_agreement_label.show()
            self.collective_agreement_input.show()
        else:
            self.collective_agreement_label.hide()
            self.collective_agreement_input.hide()
        # Update preview when toggled
        self.update_preview()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = TyosopimusApp()
    ex.show()
    sys.exit(app.exec_())
