#!/usr/bin/env python3

import sys
from PyQt5.QtWidgets import QApplication
from main import TyosopimusApp

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TyosopimusApp()
    
    print("Initial state:")
    print(f"Temp reason input visible: {window.temp_contract_reason_input.isVisible()}")
    
    print("\nDisconnecting signals temporarily...")
    window.temporary_contract_checkbox.toggled.disconnect()
    window.permanent_contract_checkbox.toggled.disconnect()
    
    print("Setting temporary checkbox to True...")
    window.temporary_contract_checkbox.setChecked(True)
    window.permanent_contract_checkbox.setChecked(False)
    
    print("Manually calling toggle_contract_type...")
    window.toggle_contract_type()
    
    print("After manual toggle:")
    print(f"Temp reason input visible: {window.temp_contract_reason_input.isVisible()}")
    
    # Try direct visibility setting
    print("\nTrying direct setVisible(True)...")
    window.temp_contract_reason_input.setVisible(True)
    window.temp_contract_reason_label.setVisible(True)
    
    print("After direct setVisible:")
    print(f"Temp reason input visible: {window.temp_contract_reason_input.isVisible()}")
    print(f"Temp reason label visible: {window.temp_contract_reason_label.isVisible()}")
