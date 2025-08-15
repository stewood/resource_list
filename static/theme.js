// Theme management system

class ThemeManager {
  constructor() {
    this.theme = localStorage.getItem('theme') || 'light';
    this.init();
  }

  init() {
    // Set initial theme
    this.setTheme(this.theme);
    
    // Remove no-flash class after a short delay to enable transitions
    setTimeout(() => {
      document.documentElement.classList.remove('no-flash');
    }, 100);
    
    // Add event listeners
    this.addEventListeners();
  }

  setTheme(theme) {
    this.theme = theme;
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    
    // Update theme toggle button
    this.updateToggleButton();
  }

  toggleTheme() {
    const newTheme = this.theme === 'light' ? 'dark' : 'light';
    this.setTheme(newTheme);
  }

  updateToggleButton() {
    const toggleBtn = document.getElementById('theme-toggle');
    if (toggleBtn) {
      const icon = toggleBtn.querySelector('i');
      if (icon) {
        icon.className = this.theme === 'light' ? 'fas fa-moon' : 'fas fa-sun';
      }
      toggleBtn.setAttribute('title', `Switch to ${this.theme === 'light' ? 'dark' : 'light'} mode`);
    }
  }

  addEventListeners() {
    // Theme toggle button
    document.addEventListener('click', (e) => {
      if (e.target.closest('#theme-toggle')) {
        e.preventDefault();
        this.toggleTheme();
      }
    });

    // Listen for HTMX requests to ensure theme persists
    document.addEventListener('htmx:afterRequest', () => {
      this.updateToggleButton();
    });
  }
}

// Initialize theme manager when DOM is loaded
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    new ThemeManager();
  });
} else {
  new ThemeManager();
}

// Export for potential use in other scripts
window.ThemeManager = ThemeManager;
