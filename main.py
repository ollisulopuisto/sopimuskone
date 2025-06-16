#!/usr/bin/env python3
import sys
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QFileDialog,
    QDateEdit,
    QFormLayout
)
from PyQt5.QtCore import QDate
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

class TyosopimusApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Työsopimus Generaattori")

        layout = QFormLayout()

        self.employee_name_input = QLineEdit()
        layout.addRow("Työntekijän nimi:", self.employee_name_input)

        self.employee_address_input = QLineEdit()
        layout.addRow("Työntekijän osoite:", self.employee_address_input)

        self.employee_id_input = QLineEdit() # Hetu
        layout.addRow("Henkilötunnus:", self.employee_id_input)

        self.employer_name_input = QLineEdit()
        layout.addRow("Työnantajan nimi:", self.employer_name_input)

        self.employer_address_input = QLineEdit()
        layout.addRow("Työnantajan osoite:", self.employer_address_input)

        self.employer_id_input = QLineEdit() # Y-tunnus
        layout.addRow("Y-tunnus:", self.employer_id_input)

        self.start_date_input = QDateEdit(calendarPopup=True)
        self.start_date_input.setDate(QDate.currentDate())
        layout.addRow("Työn alkamispäivä:", self.start_date_input)

        self.contract_type_input = QLineEdit("toistaiseksi voimassa oleva") # E.g., toistaiseksi voimassa oleva, määräaikainen
        layout.addRow("Työsopimuksen luonne:", self.contract_type_input)

        self.probation_period_input = QLineEdit("6 kuukautta") # E.g., 6 kuukautta, ei koeaikaa
        layout.addRow("Koeaika:", self.probation_period_input)

        self.job_title_input = QLineEdit()
        layout.addRow("Tehtävänimike:", self.job_title_input)

        self.main_duties_input = QLineEdit()
        layout.addRow("Pääasialliset työtehtävät:", self.main_duties_input)

        self.work_location_input = QLineEdit()
        layout.addRow("Työntekopaikka:", self.work_location_input)

        self.salary_input = QLineEdit() # Palkka euroina
        layout.addRow("Palkka (EUR/kk):", self.salary_input)

        self.salary_payment_date_input = QLineEdit("kuukauden 15. päivä")
        layout.addRow("Palkanmaksupäivä:", self.salary_payment_date_input)

        self.working_hours_input = QLineEdit("37,5 tuntia / viikko")
        layout.addRow("Säännöllinen työaika:", self.working_hours_input)

        self.annual_leave_input = QLineEdit("vuosilomalain mukaan")
        layout.addRow("Vuosiloma:", self.annual_leave_input)

        self.notice_period_input = QLineEdit("työsopimuslain mukaan")
        layout.addRow("Irtisanomisaika:", self.notice_period_input)

        self.collective_agreement_input = QLineEdit(" mahdollinen työehtosopimus") # E.g., Teknologiateollisuuden työehtosopimus
        layout.addRow("Sovellettava työehtosopimus:", self.collective_agreement_input)

        generate_button = QPushButton("Luo PDF")
        generate_button.clicked.connect(self.generate_pdf)
        layout.addRow(generate_button)

        self.setLayout(layout)

    def generate_pdf(self):
        employee_name = self.employee_name_input.text()
        employee_address = self.employee_address_input.text()
        employee_id = self.employee_id_input.text()
        employer_name = self.employer_name_input.text()
        employer_address = self.employer_address_input.text()
        employer_id = self.employer_id_input.text()
        start_date = self.start_date_input.date().toString("dd.MM.yyyy")
        contract_type = self.contract_type_input.text()
        probation_period = self.probation_period_input.text()
        job_title = self.job_title_input.text()
        main_duties = self.main_duties_input.text()
        work_location = self.work_location_input.text()
        salary = self.salary_input.text()
        salary_payment_date = self.salary_payment_date_input.text()
        working_hours = self.working_hours_input.text()
        annual_leave = self.annual_leave_input.text()
        notice_period = self.notice_period_input.text()
        collective_agreement = self.collective_agreement_input.text()

        if not all([employee_name, employer_name, start_date, salary]):
            # Basic validation: ensure essential fields are filled
            # In a real app, you'd want more robust validation and user feedback
            print("Täytä vähintään työntekijän nimi, työnantajan nimi, alkamispäivä ja palkka.")
            return

        filePath, _ = QFileDialog.getSaveFileName(self, "Tallenna PDF", "tyosopimus.pdf", "PDF Files (*.pdf)")

        if filePath:
            c = canvas.Canvas(filePath, pagesize=letter)
            c.setFont("Helvetica", 12)
            text = c.beginText(1 * inch, 10 * inch)

            text.textLine("TYÖSOPIMUS")
            text.textLine("")

            text.textLine("1. Työnantaja")
            text.textLine(f"Nimi: {employer_name}")
            text.textLine(f"Osoite: {employer_address}")
            text.textLine(f"Y-tunnus: {employer_id}")
            text.textLine("")

            text.textLine("2. Työntekijä")
            text.textLine(f"Nimi: {employee_name}")
            text.textLine(f"Osoite: {employee_address}")
            text.textLine(f"Henkilötunnus: {employee_id}")
            text.textLine("")

            text.textLine("3. Työsuhteen alkaminen ja luonne")
            text.textLine(f"Työ alkaa: {start_date}")
            text.textLine(f"Sopimuksen luonne: {contract_type}")
            text.textLine(f"Koeaika: {probation_period}")
            text.textLine("")

            text.textLine("4. Työtehtävät ja työntekopaikka")
            text.textLine(f"Tehtävänimike: {job_title}")
            text.textLine(f"Pääasialliset työtehtävät: {main_duties}")
            text.textLine(f"Työntekopaikka: {work_location}")
            text.textLine("")

            text.textLine("5. Palkkaus")
            text.textLine(f"Palkka: {salary} euroa kuukaudessa")
            text.textLine(f"Palkanmaksukausi ja -päivä: {salary_payment_date}")
            text.textLine("")

            text.textLine("6. Työaika")
            text.textLine(f"Säännöllinen työaika: {working_hours}")
            text.textLine("")

            text.textLine("7. Vuosiloma")
            text.textLine(f"Vuosiloma määräytyy: {annual_leave}")
            text.textLine("")

            text.textLine("8. Irtisanomisaika")
            text.textLine(f"Irtisanomisaika määräytyy: {notice_period}")
            text.textLine("")

            text.textLine("9. Sovellettava työehtosopimus")
            text.textLine(f"Työsuhteessa noudatetaan: {collective_agreement}")
            text.textLine("")

            text.textLine("10. Muut ehdot")
            text.textLine("Lorem ipsum dolor sit amet, consectetur adipiscing elit. ...") # Placeholder
            text.textLine("")

            text.textLine("Allekirjoitukset")
            text.textLine("")
            text.textLine("_________________________                               _________________________")
            text.textLine(f"{employer_name}                                        {employee_name}")
            text.textLine("(Työnantaja)                                         (Työntekijä)")

            c.drawText(text)
            c.save()
            print(f"PDF luotu: {filePath}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = TyosopimusApp()
    ex.show()
    sys.exit(app.exec_())
