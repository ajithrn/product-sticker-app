document.addEventListener('DOMContentLoaded', function() {
  const toggles = document.querySelectorAll('.custom-control-input[type="checkbox"]');
  const printerTypeSelect = document.getElementById('printer_type');
  const normalPrinterSettings = document.getElementById('normal_printer_settings');
  const paperSizeSelect = document.getElementById('paper_size');
  const customPaperSize = document.getElementById('custom_paper_size');

  /**
   * Toggles the visibility of an element.
   * @param {HTMLElement} element - The element to change visibility for.
   * @param {boolean} show - Whether to show (true) or hide (false) the element.
   */
  function toggleVisibility(element, show) {
      if (element) {
          if (show) {
              element.classList.remove('d-none');
              element.classList.add('d-block');
          } else {
              element.classList.remove('d-block');
              element.classList.add('d-none');
          }
      }
  }

  /**
   * Updates the visibility of the normal printer settings based on the selected printer type.
   */
  function updatePrinterSettings() {
      if (printerTypeSelect) {
          toggleVisibility(normalPrinterSettings, printerTypeSelect.value === 'normal');
      }
  }

  /**
   * Updates the visibility of custom paper size settings based on the selected paper size.
   */
  function updatePaperSizeSettings() {
      if (paperSizeSelect) {
          toggleVisibility(customPaperSize, paperSizeSelect.value === 'custom');
      }
  }

  // Add change event listeners for each toggle to enable/disable input fields.
  toggles.forEach(toggle => {
      toggle.addEventListener('change', function() {
          const row = this.closest('.row');
          if (row) {
              const headingTextInput = row.querySelector('textarea, input[type="text"]');
              const fontSizeInput = row.querySelector('input[type="number"]');

              if (headingTextInput) {
                  headingTextInput.disabled = !this.checked;
              }

              if (fontSizeInput) {
                  fontSizeInput.disabled = !this.checked;
              }
          }
      });
      // Initialize state.
      toggle.dispatchEvent(new Event('change'));
  });

  // Add change event listeners for printer type and paper size select elements if they exist.
  if (printerTypeSelect) {
      printerTypeSelect.addEventListener('change', updatePrinterSettings);
  }
  if (paperSizeSelect) {
      paperSizeSelect.addEventListener('change', updatePaperSizeSettings);
  }

  // Initialize state on page load.
  updatePrinterSettings();
  updatePaperSizeSettings();
});
