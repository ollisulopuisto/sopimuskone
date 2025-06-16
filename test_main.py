import sys
import unittest
from unittest.mock import patch, MagicMock, ANY # Added ANY
import os
import json
from PyQt5.QtWidgets import QApplication, QLineEdit, QTextEdit, QDateEdit, QComboBox
from PyQt5.QtCore import QDate
from reportlab.lib.pagesizes import letter # Added letter

# Assuming main.py is in the same directory or accessible in PYTHONPATH
from main import TyosopimusApp

TEST_CONTRACT_FILE = "test_contracts.json"

# We need a QApplication instance to run Qt-dependent tests, even if the GUI isn't shown.
# It's good practice to create it once for all tests in this module.
app = QApplication.instance() # Check if an instance already exists
if app is None: # Create it if it doesn't
    app = QApplication(sys.argv)

class TestTyosopimusApp(unittest.TestCase):

    def setUp(self):
        """Set up for each test. This runs before each test method."""
        # Ensure a clean state for contract storage for each test
        if os.path.exists(TEST_CONTRACT_FILE):
            os.remove(TEST_CONTRACT_FILE)
        # Pass the test-specific contract file to the app
        self.window = TyosopimusApp(contracts_file=TEST_CONTRACT_FILE)

    def tearDown(self):
        """Clean up after each test. This runs after each test method."""
        if os.path.exists(TEST_CONTRACT_FILE):
            os.remove(TEST_CONTRACT_FILE)
        self.window.close() # Close the window if it was shown
        # QApplication.quit() # Avoid quitting QApplication here if it's shared across tests

    def test_initial_state(self):
        """Test the initial state of the application's UI elements."""
        self.assertEqual(self.window.employee_name_input.text(), "")
        self.assertEqual(self.window.employer_name_input.text(), "")
        self.assertEqual(self.window.contract_type_input.text(), "toistaiseksi voimassa oleva")
        self.assertTrue(self.window.contract_selector.count() == 1) # Only "Uusi sopimus"
        self.assertIn("TYÖSOPIMUS", self.window.preview_area.toHtml()) # Basic check for preview content

    def test_get_contract_details_as_dict(self):
        """Test retrieving data from input fields."""
        self.window.employee_name_input.setText("Testi Työntekijä")
        self.window.employer_name_input.setText("Testi Työnantaja")
        self.window.salary_input.setText("3000")
        self.window.start_date_input.setDate(QDate(2025, 7, 1))
        self.window.muut_ehdot_input.setPlainText("Testi ehtoja.\nToinen rivi.")

        details = self.window.get_contract_data()

        self.assertEqual(details["employee_name"], "Testi Työntekijä")
        self.assertEqual(details["employer_name"], "Testi Työnantaja")
        self.assertEqual(details["salary"], "3000")
        self.assertEqual(details["start_date"], "01.07.2025")
        self.assertEqual(details["muut_ehdot"], "Testi ehtoja.\nToinen rivi.")

    def test_save_and_load_contract(self):
        """Test saving a contract and then loading it."""
        # 1. Populate fields
        self.window.employee_name_input.setText("Virtanen Matti")
        self.window.employer_name_input.setText("Firma Oy")
        self.window.job_title_input.setText("Ohjelmistokehittäjä")
        self.window.salary_input.setText("4000")
        self.window.start_date_input.setDate(QDate(2025, 8, 15))
        self.window.muut_ehdot_input.setPlainText("Etätyömahdollisuus.")

        # 2. Save contract
        self.window.save_contract()
        # The file name is generated as below
        expected_file = "Virtanen Matti_Firma Oy_tyosopimus.json"
        self.assertTrue(os.path.exists(expected_file))
        with open(expected_file, 'r', encoding='utf-8') as f:
            loaded_data_from_file = json.load(f)
        self.assertEqual(loaded_data_from_file["employee_name"], "Virtanen Matti")

        # 3. Check if it's in the combo box
        self.assertEqual(self.window.contract_selector.count(), 2) # "Uusi sopimus" + 1 saved
        self.assertIn("Virtanen Matti", self.window.contract_selector.itemText(1))

        # 4. Select the saved contract from combo to load it
        self.window.contract_selector.setCurrentIndex(1)

        # 5. Verify fields are populated correctly
        self.assertEqual(self.window.employee_name_input.text(), "Virtanen Matti")
        self.assertEqual(self.window.employer_name_input.text(), "Firma Oy")
        self.assertEqual(self.window.job_title_input.text(), "Ohjelmistokehittäjä")
        self.assertEqual(self.window.salary_input.text(), "4000")
        self.assertEqual(self.window.start_date_input.date().toString("dd.MM.yyyy"), "15.08.2025")
        self.assertEqual(self.window.muut_ehdot_input.toPlainText(), "Etätyömahdollisuus.")

        # Clean up the created contract file
        if os.path.exists(expected_file):
            os.remove(expected_file)

    def test_html_preview_generation(self):
        """Test that HTML preview is generated and contains expected elements."""
        self.window.employee_name_input.setText("Esimerkki Henkilö")
        self.window.employer_name_input.setText("Esimerkki Yritys")
        self.window.job_title_input.setText("Testaaja")
        self.window.muut_ehdot_input.setPlainText("Tämä on testi.\\nRivinvaihto.")
        self.window.update_preview()
        
        # Use toPlainText() for more robust assertions against visible text
        plain_text_content = self.window.preview_area.toPlainText()

        self.assertIn("TYÖSOPIMUS", plain_text_content)
        self.assertIn("Esimerkki Yritys", plain_text_content)
        self.assertIn("Esimerkki Henkilö", plain_text_content)
        self.assertIn("Testaaja", plain_text_content)
        # For multi-line, toPlainText() preserves newlines
        self.assertIn("Tämä on testi.\nRivinvaihto.", plain_text_content)

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
        self.window.salary_input.setText("5000")
        self.window.job_title_input.setText("Ohjelmistokehittäjä")
        self.window.muut_ehdot_input.setPlainText("Lisäehto 1\nToinen lisäehto.")
        self.window.generate_pdf()
        mock_doc_instance.build.assert_called_once()
        # Check that the story contains expected Paragraphs
        story = mock_doc_instance.build.call_args[0][0]
        story_texts = " ".join(str(getattr(p, 'text', '')) for p in story)
        self.assertIn("Testi Työnantaja Oy", story_texts)
        self.assertIn("Testi Työntekijä", story_texts)
        self.assertIn("01.01.2023", story_texts)
        self.assertIn("5000 euroa kuukaudessa", story_texts)
        self.assertIn("Ohjelmistokehittäjä", story_texts)
        self.assertIn("Lisäehto 1", story_texts)
        self.assertIn("Toinen lisäehto.", story_texts)

    def test_required_field_styling(self):
        """Test that required fields have the correct styling applied."""
        # Check that required fields have orange border styling
        required_style = "border: 2px solid #FFA500"
        self.assertIn(required_style, self.window.employer_name_input.styleSheet())
        self.assertIn(required_style, self.window.employee_name_input.styleSheet())
        self.assertIn(required_style, self.window.start_date_input.styleSheet())
        self.assertIn(required_style, self.window.salary_input.styleSheet())
        
        # Check that non-required fields don't have this styling
        self.assertNotIn(required_style, self.window.employer_address_input.styleSheet())
        self.assertNotIn(required_style, self.window.employee_address_input.styleSheet())

    def test_contract_name_generation(self):
        """Test that contract names are generated correctly from employee and employer names."""
        self.window.employee_name_input.setText("Matti Virtanen")
        self.window.employer_name_input.setText("Test Company Oy")
        
        # Mock the save contract method to capture the filename
        with patch('main.QMessageBox.warning') as mock_warning:
            with patch('builtins.open', create=True) as mock_open:
                with patch('os.makedirs') as mock_makedirs:
                    self.window.save_contract()
                    # Should not show warning for missing contract name since it's auto-generated
                    mock_warning.assert_not_called()

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
        
        contract_data = self.window.get_contract_data()
        self.assertEqual(contract_data["start_date"], "25.12.2025")
        
        # Update preview and check date formatting
        self.window.update_preview()
        preview_text = self.window.preview_area.toPlainText()
        self.assertIn("25.12.2025", preview_text)

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


if __name__ == '__main__':
    unittest.main()
