function changeLanguage(lang) {
  localStorage.setItem('selectedLang', lang);
  
  // Try to find the google translate dropdown
  const selectField = document.querySelector(".goog-te-combo");
  if (selectField) {
    selectField.value = lang;
    selectField.dispatchEvent(new Event('change'));
  } else {
    // If google translate hasn't loaded yet, retry after a delay
    setTimeout(() => {
      const retrySelect = document.querySelector(".goog-te-combo");
      if (retrySelect) {
        retrySelect.value = lang;
        retrySelect.dispatchEvent(new Event('change'));
      }
    }, 1000);
  }
}

function initLanguage() {
  const savedLang = localStorage.getItem('selectedLang') || 'en';
  const select = document.getElementById('languageSelect');
  if (select) {
    select.value = savedLang;
  }
  
  // Wait a bit for the Google Translate widget to inject itself into the DOM
  setTimeout(() => {
    if (savedLang !== 'en') {
      changeLanguage(savedLang);
    }
  }, 500);
}

document.addEventListener('DOMContentLoaded', initLanguage);
