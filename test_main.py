import sys
import unittest
from unittest.mock import patch, MagicMock, ANY, mock_open as unittest_mock_open # Added mock_open
import os
import json
from PyQt5.QtWidgets import QApplication, QLineEdit, QTextEdit, QDateEdit, QComboBox, QCheckBox, QMessageBox # Added QMessageBox
from PyQt5.QtCore import QDate
from reportlab.lib.pagesizes import letter # Added letter

# Assuming main.py is in the same directory or accessible in PYTHONPATH
from main import TyosopimusApp

# TEST_CONTRACT_FILE = "test_contracts.json" # No longer needed, using a directory
# TEST_CONTRACTS_DIR = os.path.expanduser("~/Documents/sopimuskone_test_contracts") # Old path
TEST_CONTRACTS_DIR = os.path.join(os.getcwd(), "test_contracts_temp") # New path within pwd

# We need a QApplication instance to run Qt-dependent tests, even if the GUI isn't shown.
# It's good practice to create it once for all tests in this module.
app = QApplication.instance() # Check if an instance already exists
if app is None: # Create it if it doesn't
    app = QApplication(sys.argv)

class TestTyosopimusApp(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Set the TESTING environment variable for all tests in this class
        os.environ["TESTING"] = "True"
        # Ensure the test contracts directory exists and is empty
        if not os.path.exists(TEST_CONTRACTS_DIR):
            os.makedirs(TEST_CONTRACTS_DIR)
        else:
            # Clear out any pre-existing files from previous runs
            for f in os.listdir(TEST_CONTRACTS_DIR):
                os.remove(os.path.join(TEST_CONTRACTS_DIR, f))

    @classmethod
    def tearDownClass(cls):
        # Clean up the TESTING environment variable
        if "TESTING" in os.environ:
            del os.environ["TESTING"]
        # Clean up the test contracts directory and its contents
        if os.path.exists(TEST_CONTRACTS_DIR):
            for f in os.listdir(TEST_CONTRACTS_DIR):
                try:
                    os.remove(os.path.join(TEST_CONTRACTS_DIR, f))
                except OSError:
                    pass # Ignore if file is already gone or other issues
            try:
                os.rmdir(TEST_CONTRACTS_DIR)
            except OSError:
                pass # Ignore if directory is already gone or not empty (should be empty)

    def setUp(self):
        """Set up for each test. This runs before each test method."""
        # Clean the test directory before each test to ensure isolation
        for f in os.listdir(TEST_CONTRACTS_DIR):
            os.remove(os.path.join(TEST_CONTRACTS_DIR, f))
        self.window = TyosopimusApp()

    def tearDown(self):
        """Clean up after each test. This runs after each test method."""
        self.window.close() # Close the window if it was shown
        # Clean the test directory after each test
        for f in os.listdir(TEST_CONTRACTS_DIR):
            os.remove(os.path.join(TEST_CONTRACTS_DIR, f))

    def test_initial_state(self):
        """Test the initial state of the application's UI elements."""
        self.assertEqual(self.window.employee_name_input.text(), "")
        self.assertEqual(self.window.employer_name_input.text(), "")
        self.assertTrue(self.window.permanent_contract_radio.isChecked())
        self.assertFalse(self.window.temporary_contract_radio.isChecked())
        self.assertEqual(self.window.contract_date_input.date().toString("dd.MM.yyyy"), QDate.currentDate().toString("dd.MM.yyyy")) # Added for contract_date
        self.assertTrue(self.window.contract_selector.count() == 1) # Only "Uusi sopimus"
        self.assertIn("TYÖSOPIMUS", self.window.preview_area.toHtml()) # Basic check for preview content

    def test_get_contract_details_as_dict(self):
        """Test retrieving data from input fields."""
        self.window.employee_name_input.setText("Testi Työntekijä")
        self.window.employer_name_input.setText("Testi Työnantaja")
        self.window.salary_input.setText("3000")
        self.window.start_date_input.setDate(QDate(2025, 7, 1))
        self.window.contract_date_input.setDate(QDate(2025, 6, 15)) # Added for contract_date
        self.window.muut_ehdot_input.setPlainText("Testi ehtoja.\nToinen rivi.")

        details = self.window.get_contract_data()

        self.assertEqual(details["employee_name"], "Testi Työntekijä")
        self.assertEqual(details["employer_name"], "Testi Työnantaja")
        self.assertEqual(details["salary"], "3000")
        self.assertEqual(details["start_date"], "01.07.2025")
        self.assertEqual(details["contract_date"], "15.06.2025") # Added for contract_date
        self.assertEqual(details["muut_ehdot"], "Testi ehtoja.\nToinen rivi.")

    def test_save_and_load_contract(self):
        """Test saving a contract and then loading it."""
        # 1. Populate fields
        employee_name = "Virtanen Matti"
        employer_name = "Firma Oy"
        self.window.employee_name_input.setText(employee_name)
        self.window.employer_name_input.setText(employer_name)
        self.window.job_title_input.setText("Ohjelmistokehittäjä")
        self.window.salary_input.setText("4000")
        self.window.start_date_input.setDate(QDate(2025, 8, 15))
        self.window.contract_date_input.setDate(QDate(2025, 8, 1)) # Added for contract_date
        self.window.muut_ehdot_input.setPlainText("Etätyömahdollisuus.")

        # 2. Save contract
        with patch('main.QMessageBox.question', return_value=QMessageBox.Yes): # Assume user confirms overwrite if needed
            self.window.save_contract()
        
        # Find the saved file - name includes timestamp, so we need to list dir
        saved_files = os.listdir(TEST_CONTRACTS_DIR)
        self.assertEqual(len(saved_files), 1, "More than one file found in test contracts dir after saving")
        saved_filename = saved_files[0]
        expected_file_path = os.path.join(TEST_CONTRACTS_DIR, saved_filename)

        self.assertTrue(os.path.exists(expected_file_path))
        with open(expected_file_path, 'r', encoding='utf-8') as f:
            loaded_data_from_file = json.load(f)
        self.assertEqual(loaded_data_from_file["employee_name"], employee_name)

        # 3. Check if it's in the combo box (app reloads contracts after save)
        # self.window.load_contracts() # This is now done by save_contract
        self.assertEqual(self.window.contract_selector.count(), 2) # "Uusi sopimus" + 1 saved
        # The display name includes date, so we check for employee and employer name parts
        new_contract_display_name = self.window.contract_selector.itemText(1)
        self.assertIn(employee_name, new_contract_display_name)
        self.assertIn(employer_name, new_contract_display_name)

        # 4. Select the saved contract from combo to load it
        self.window.contract_selector.setCurrentIndex(1)

        # 5. Verify fields are populated correctly
        self.assertEqual(self.window.employee_name_input.text(), employee_name)
        self.assertEqual(self.window.employer_name_input.text(), employer_name)
        self.assertEqual(self.window.job_title_input.text(), "Ohjelmistokehittäjä")
        self.assertEqual(self.window.salary_input.text(), "4000")
        self.assertEqual(self.window.start_date_input.date().toString("dd.MM.yyyy"), "15.08.2025")
        self.assertEqual(self.window.contract_date_input.date().toString("dd.MM.yyyy"), "01.08.2025") # Added for contract_date
        self.assertEqual(self.window.muut_ehdot_input.toPlainText(), "Etätyömahdollisuus.")

        # Clean up is handled by tearDown and tearDownClass

    def test_html_preview_generation(self):
        """Test that HTML preview is generated and contains expected elements."""
        self.window.employee_name_input.setText("Esimerkki Henkilö")
        self.window.employer_name_input.setText("Esimerkki Yritys")
        self.window.job_title_input.setText("Testaaja")
        self.window.contract_date_input.setDate(QDate(2025, 1, 1)) # Added for contract_date
        self.window.muut_ehdot_input.setPlainText("Tämä on testi.\nRivinvaihto.")
        self.window.update_preview()
        
        # Use toPlainText() for more robust assertions against visible text
        plain_text_content = self.window.preview_area.toPlainText()

        self.assertIn("TYÖSOPIMUS", plain_text_content)
        self.assertIn("Sopimuspäivämäärä: 01.01.2025", plain_text_content) # Added for contract_date
        self.assertIn("Esimerkki Yritys", plain_text_content)
        self.assertIn("Esimerkki Henkilö", plain_text_content)
        self.assertIn("Testaaja", plain_text_content)
        # The HTML preview converts newlines to spaces or removes them
        self.assertIn("Tämä on testi.", plain_text_content)
        self.assertIn("Rivinvaihto.", plain_text_content)

    def test_pdf_generation_path_creation(self):
        """Test that the PDF generation logic attempts to create a PDF using Platypus."""
        self.window.employee_name_input.setText("PDF Testi")
        self.window.employer_name_input.setText("PDF Työnantaja")
        self.window.salary_input.setText("3000")
        with patch('main.QFileDialog.getSaveFileName', return_value=("test_sopimus.pdf", "PDF Files (*.pdf)")) as mock_get_save_file_name:
            with patch('main.SimpleDocTemplate') as mock_doc_class:
                mock_doc_instance = mock_doc_class.return_value
                mock_doc_instance.build = MagicMock()
                self.window.generate_pdf()
                mock_get_save_file_name.assert_called_once()
                mock_doc_class.assert_called_once_with("test_sopimus.pdf", pagesize=letter, rightMargin=ANY, leftMargin=ANY, topMargin=ANY, bottomMargin=ANY)
                mock_doc_instance.build.assert_called_once()

    @patch('main.QFileDialog.getSaveFileName')
    @patch('main.SimpleDocTemplate')
    def test_pdf_generation_data_effects(self, mock_doc_class, mock_get_save_file_name):
        """Test that data from fields is correctly passed to PDF generation (Platypus version)."""
        mock_get_save_file_name.return_value = ("dummy.pdf", "PDF Files (*.pdf)")
        mock_doc_instance = mock_doc_class.return_value
        mock_doc_instance.build = MagicMock()
        self.window.employer_name_input.setText("Testi Työnantaja Oy")
        self.window.employee_name_input.setText("Testi Työntekijä")
        self.window.start_date_input.setDate(QDate(2023, 1, 1))
        self.window.contract_date_input.setDate(QDate(2022, 12, 15)) # Added for contract_date
        self.window.salary_input.setText("5000")
        self.window.job_title_input.setText("Ohjelmistokehittäjä")
        self.window.muut_ehdot_input.setPlainText("Lisäehto 1\nToinen lisäehto.")
        self.window.generate_pdf()
        mock_doc_instance.build.assert_called_once()
        # Check that the story contains expected data (more robust than exact text matching)
        story = mock_doc_instance.build.call_args[0][0]
        story_texts = " ".join(str(getattr(p, 'text', '')) for p in story)
        # Test for key contract data without being too specific about formatting
        self.assertIn("Testi Työnantaja Oy", story_texts)
        self.assertIn("Testi Työntekijä", story_texts)
        self.assertIn("01.01.2023", story_texts)  # Start date
        self.assertIn("5000", story_texts)  # Salary amount
        self.assertIn("Ohjelmistokehittäjä", story_texts)  # Job title
        self.assertIn("Lisäehto 1", story_texts)  # Custom conditions

    def test_required_field_styling(self):
        """Test that required fields have the correct styling applied."""
        # Check that required fields have orange border styling
        required_style = "border: 2px solid #FFA500"
        self.assertIn(required_style, self.window.employer_name_input.styleSheet())
        self.assertIn(required_style, self.window.employee_name_input.styleSheet())
        self.assertIn(required_style, self.window.start_date_input.styleSheet())
        self.assertIn(required_style, self.window.salary_input.styleSheet())
        self.assertIn(required_style, self.window.contract_date_input.styleSheet()) # Added for contract_date
        
        # Check that non-required fields don't have this styling
        self.assertNotIn(required_style, self.window.employer_address_input.styleSheet())
        self.assertNotIn(required_style, self.window.employee_address_input.styleSheet())

    def test_contract_name_generation(self):
        """Test that contract names are generated correctly from employee and employer names."""
        self.window.employee_name_input.setText("Matti Virtanen")
        self.window.employer_name_input.setText("Test Company Oy")
        
        # Mock the save contract method to capture the filename
        # Simulate user choosing not to overwrite if prompted (though unlikely with timestamps)
        with patch('main.QMessageBox.question', return_value=QMessageBox.Yes) as mock_question: 
            with patch('builtins.open', unittest_mock_open()) as mock_open_file: # Use new_callable
                with patch('os.makedirs') as mock_makedirs: # Mock makedirs
                    self.window.save_contract()
                    
                    # Assert that makedirs was called if the directory didn't exist initially
                    # This is tricky to assert reliably without knowing pre-test state, 
                    # but we can check it's called with the correct path if it is called.
                    if mock_makedirs.called:
                        mock_makedirs.assert_called_with(TEST_CONTRACTS_DIR, exist_ok=True) # main.py uses os.makedirs without exist_ok=True, but it's fine for test

                    # Assert that open was called to write a file
                    mock_open_file.assert_called()
                    args, _ = mock_open_file.call_args
                    filepath = args[0]
                    self.assertTrue(filepath.startswith(TEST_CONTRACTS_DIR))
                    self.assertTrue(filepath.endswith(".json"))
                    # Check that the filename contains sanitized employee and employer names and a timestamp
                    self.assertIn("MattiVirtanen", os.path.basename(filepath).replace(" ", ""))
                    self.assertIn("TestCompanyOy", os.path.basename(filepath).replace(" ", ""))
                    self.assertRegex(os.path.basename(filepath), r'\d{8}_\d{6}\.json$') # Timestamp check

    def test_empty_required_fields_validation(self):
        """Test behavior when required fields are empty during PDF generation."""
        # Leave required fields empty
        self.window.employee_name_input.setText("")
        self.window.employer_name_input.setText("")
        self.window.salary_input.setText("")
        
        with patch('main.QFileDialog.getSaveFileName', return_value=("test.pdf", "PDF Files (*.pdf)")):
            with patch('main.SimpleDocTemplate') as mock_doc_class:
                mock_doc_instance = mock_doc_class.return_value
                mock_doc_instance.build = MagicMock()
                
                # PDF generation should still work, just with empty values
                self.window.generate_pdf()
                mock_doc_instance.build.assert_called_once()

    def test_special_characters_in_contract_data(self):
        """Test handling of special characters and unicode in contract data."""
        # Set fields with special characters
        self.window.employee_name_input.setText("Mätti Öystilä")
        self.window.employer_name_input.setText("Åbo Företag Oy")
        self.window.job_title_input.setText("Ohjelmistokehittäjä & Suunnittelija")
        self.window.muut_ehdot_input.setPlainText("Erityisehdot: €1000 bonus\nÄ, Ö, Å characters")
        
        # Test that preview updates without errors
        self.window.update_preview()
        preview_text = self.window.preview_area.toPlainText()
        self.assertIn("Mätti Öystilä", preview_text)
        self.assertIn("Åbo Företag Oy", preview_text)
        self.assertIn("€1000 bonus", preview_text)

    def test_date_formatting(self):
        """Test that dates are formatted correctly in different contexts."""
        test_date = QDate(2025, 12, 25)
        self.window.start_date_input.setDate(test_date)
        self.window.contract_date_input.setDate(test_date) # Added for contract_date
        
        contract_data = self.window.get_contract_data()
        self.assertEqual(contract_data["start_date"], "25.12.2025")
        self.assertEqual(contract_data["contract_date"], "25.12.2025") # Added for contract_date
        
        # Update preview and check date formatting
        self.window.update_preview()
        preview_text = self.window.preview_area.toPlainText()
        self.assertIn("25.12.2025", preview_text)
        self.assertIn("Sopimuspäivämäärä: 25.12.2025", preview_text) # Added for contract_date

    def test_contract_loading_edge_cases(self):
        """Test contract loading with edge cases like missing or corrupted files."""
        # Test with non-existent contracts directory
        self.window.contracts_dir = "non_existent_contracts"
        self.window.load_contracts()
        # Should not crash, should have empty contracts
        self.assertEqual(len(self.window.contracts), 0)
        # Should always have "Uusi sopimus" as first item
        self.assertEqual(self.window.contract_selector.itemText(0), "Uusi sopimus")
        # Should only have one item when no contracts are saved
        self.assertEqual(self.window.contract_selector.count(), 1)

    def test_malformed_contract_json_is_sanitized_on_load(self):
        """A contract file with wrong-typed fields must not crash the app.

        Loaded JSON is untrusted input; non-string values previously reached
        Qt setters / string operations and aborted the app with a TypeError.
        """
        hostile = os.path.join(TEST_CONTRACTS_DIR, "hostile.json")
        with open(hostile, "w", encoding="utf-8") as f:
            json.dump({
                "employee_name": 12345,
                "employer_name": "Firma Oy",
                "salary": 5,
                "display_name": 99,
                "has_collective_agreement": "yes",
            }, f)

        # load_contracts() fires the combo's currentIndexChanged slot, so a
        # regression here aborts the process; this call is the regression gate.
        self.window.load_contracts()

        loaded = self.window.contracts.get("hostile")
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["employee_name"], "")
        self.assertEqual(loaded["salary"], "")
        self.assertEqual(loaded["display_name"], "")
        self.assertIs(loaded["has_collective_agreement"], False)
        # Well-typed values are preserved untouched
        self.assertEqual(loaded["employer_name"], "Firma Oy")

    def test_mixed_timezone_created_at_does_not_abort_contract_sorting(self):
        """Untrusted created_at values must never break startup sorting.

        Contract files are untrusted, so they can mix timezone-aware and naive
        ISO timestamps. Comparing those raises TypeError inside load_contracts()
        and prevents the app from starting at all.
        """
        for name, stamp in (("naive", "2024-01-01T00:00:00"),
                            ("aware", "2024-02-01T00:00:00+02:00")):
            with open(os.path.join(TEST_CONTRACTS_DIR, name + ".json"), "w",
                      encoding="utf-8") as f:
                json.dump({"employee_name": name, "created_at": stamp}, f)

        self.window.load_contracts()

        self.assertIn("naive", self.window.contracts)
        self.assertIn("aware", self.window.contracts)
        # Newest first: the aware timestamp is still the later of the two.
        self.assertIn("aware", self.window.contract_selector.itemText(1))

    def test_deeply_nested_contract_json_is_skipped(self):
        """Pathologically nested JSON must be skipped, not abort startup."""
        with open(os.path.join(TEST_CONTRACTS_DIR, "deep.json"), "w",
                  encoding="utf-8") as f:
            f.write('{"employee_name": "Deep", "x": '
                    + "[" * 200000 + "]" * 200000 + "}")

        self.window.load_contracts()

        self.assertNotIn("deep", self.window.contracts)
        self.assertEqual(self.window.contract_selector.count(), 1)

    def test_contract_type_radio_buttons(self):
        """Test the contract type radio button functionality (logic only, not widget visibility)."""
        # Initially, permanent should be checked, temporary unchecked
        self.assertTrue(self.window.permanent_contract_radio.isChecked())
        self.assertFalse(self.window.temporary_contract_radio.isChecked())
        data = self.window.get_contract_data()
        self.assertEqual(data["contract_type"], "toistaiseksi voimassa oleva")
        self.assertFalse(data["is_temporary"])
        # Switch to temporary contract
        self.window.temporary_contract_radio.setChecked(True)
        self.window.toggle_contract_type()
        self.assertTrue(self.window.temporary_contract_radio.isChecked())
        self.assertFalse(self.window.permanent_contract_radio.isChecked())
        data = self.window.get_contract_data()
        self.assertEqual(data["contract_type"], "määräaikainen")
        self.assertTrue(data["is_temporary"])
        # Switch back to permanent
        self.window.permanent_contract_radio.setChecked(True)
        self.window.toggle_contract_type()
        self.assertTrue(self.window.permanent_contract_radio.isChecked())
        self.assertFalse(self.window.temporary_contract_radio.isChecked())
        data = self.window.get_contract_data()
        self.assertEqual(data["contract_type"], "toistaiseksi voimassa oleva")
        self.assertFalse(data["is_temporary"])

    def test_temporary_contract_data_handling(self):
        """Test that temporary contract data is properly handled."""
        # Set up temporary contract and manually trigger the toggle
        self.window.temporary_contract_radio.setChecked(True)
        self.window.toggle_contract_type()  # Manually trigger what the signal would do
        self.window.temp_contract_reason_input.setText("Sijaisuus")
        self.window.end_date_input.setDate(QDate(2025, 12, 31))
        # Get contract data
        data = self.window.get_contract_data()
        # Check that temporary contract data is correctly captured
        self.assertEqual(data["contract_type"], "määräaikainen")
        self.assertTrue(data["is_temporary"])
        self.assertEqual(data["temp_contract_reason"], "Sijaisuus")
        self.assertEqual(data["end_date"], "31.12.2025")

    def test_update_preview_escapes_html_metacharacters(self):
        """User-supplied HTML metacharacters must be escaped in the live preview.

        Contract data is rendered with QTextEdit.setHtml(), so unescaped '<', '>',
        '&' from user input would be interpreted as markup (spoofable contract
        content, silently dropped text).
        """
        self.window.employee_name_input.setText("Matti <b>Virtanen</b>")
        self.window.employer_name_input.setText("Yhtiö & Co")
        self.window.job_title_input.setText("Kehittäjä <script>alert(1)</script>")
        self.window.muut_ehdot_input.setPlainText("Ehto: x < y & z")
        self.window.update_preview()

        html = self.window.preview_area.toHtml()

        # User markup is escaped, never rendered as HTML
        self.assertIn("&lt;b&gt;Virtanen&lt;/b&gt;", html)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html)
        self.assertIn("Yhtiö &amp; Co", html)
        self.assertIn("Ehto: x &lt; y &amp; z", html)
        # Raw user markup must not appear in the rendered HTML
        self.assertNotIn("<b>Virtanen</b>", html)
        self.assertNotIn("<script>alert(1)</script>", html)
        # The underlying data still round-trips intact as plain text
        plain = self.window.preview_area.toPlainText()
        self.assertIn("Matti <b>Virtanen</b>", plain)
        self.assertIn("Yhtiö & Co", plain)
        self.assertIn("Ehto: x < y & z", plain)

    def test_update_preview_converts_newlines_to_line_breaks(self):
        """Multiline free-text must become <br /> after HTML escaping."""
        self.window.muut_ehdot_input.setPlainText("Ehto 1\nEhto 2\nEhto 3")
        self.window.update_preview()
        html = self.window.preview_area.toHtml()
        self.assertIn("Ehto 1<br />Ehto 2<br />Ehto 3", html)

    @patch('main.QMessageBox.information')
    @patch('main.SimpleDocTemplate')
    @patch('main.QFileDialog.getSaveFileName')
    def test_generate_pdf_escapes_html_metacharacters(
        self, mock_get_save_file_name, mock_doc_class, mock_info
    ):
        """User-supplied data embedded in reportlab Paragraph markup must be escaped."""
        mock_get_save_file_name.return_value = ("dummy.pdf", "PDF Files (*.pdf)")
        mock_doc_instance = mock_doc_class.return_value
        mock_doc_instance.build = MagicMock()
        self.window.main_duties_input.setText("Koodausta <b>ja</b> suunnittelua")
        self.window.generate_pdf()

        story = mock_doc_instance.build.call_args[0][0]
        duty_texts = [item.text for item in story
                      if hasattr(item, "text") and "Koodausta" in item.text]
        self.assertTrue(duty_texts, "main_duties paragraph not found in PDF story")
        self.assertNotIn("<b>ja</b>", duty_texts[0])
        self.assertIn("&lt;b&gt;ja&lt;/b&gt;", duty_texts[0])

    def test_new_salary_fields(self):
        """Test that the new salary fields work correctly."""
        # Set salary and basis
        self.window.salary_input.setText("3500 EUR/kk")
        self.window.salary_basis_input.setText("kuukausipalkka")
        # Get contract data
        data = self.window.get_contract_data()
        # Check that the data is captured correctly
        self.assertEqual(data["salary"], "3500 EUR/kk")
        self.assertEqual(data["salary_basis"], "kuukausipalkka")
        # Check that the preview contains the new field labels
        self.window.update_preview()
        preview_text = self.window.preview_area.toPlainText()
        self.assertIn("Työstä maksettava palkka tai muu vastike:", preview_text)
        self.assertIn("Palkan määräytymisen peruste:", preview_text)


    def test_bulk_field_updates_render_preview_once(self):
        """Bulk field updates must render the preview once, not once per field."""
        with patch.object(self.window.preview_area, "setHtml") as mock_set_html:
            self.window.clear_fields()
            self.assertEqual(mock_set_html.call_count, 1)

        data = {
            "employee_name": "Matti Meikäläinen",
            "employer_name": "Acme Oy",
            "muut_ehdot": "Eka rivi\nToka rivi",
        }
        with patch.object(self.window.preview_area, "setHtml") as mock_set_html:
            self.window.populate_fields(data)
            self.assertEqual(mock_set_html.call_count, 1)

        # The single render must reflect the final field values.
        self.window.populate_fields(data)
        preview_text = self.window.preview_area.toPlainText()
        self.assertIn("Matti Meikäläinen", preview_text)
        self.assertIn("Eka rivi", preview_text)


if __name__ == '__main__':
    unittest.main()
