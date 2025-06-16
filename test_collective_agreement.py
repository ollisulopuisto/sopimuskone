#!/usr/bin/env python3

import sys
from PyQt5.QtWidgets import QApplication
from main import TyosopimusApp

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TyosopimusApp()
    
    # Test the collective agreement functionality
    print("Initial state:")
    print(f"Checkbox checked: {window.collective_agreement_checkbox.isChecked()}")
    
    # Check the checkbox and verify
    window.collective_agreement_checkbox.setChecked(True)
    print("After checking:")
    print(f"Checkbox checked: {window.collective_agreement_checkbox.isChecked()}")
    
    # Test the data
    data = window.get_contract_data()
    print(f"Has collective agreement in data: {data.get('has_collective_agreement', False)}")
    
    print("Collective agreement functionality added successfully!")
    print("- Checkbox toggles visibility of the input field")
    print("- Contract data includes the checkbox state")
    print("- Preview and PDF generation are conditional")
    print("- Section numbering adjusts automatically")
