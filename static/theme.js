// Theme management system

class ThemeManager {
  constructor() {
    this.theme = localStorage.getItem('theme') || 'dark';
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

// Location Search functionality
class LocationSearchManager {
  constructor() {
    this.init();
  }

  init() {
    this.addEventListeners();
  }

  addEventListeners() {
    // Geocode button click
    document.addEventListener('click', (e) => {
      if (e.target.closest('#geocodeBtn')) {
        e.preventDefault();
        this.geocodeAddress();
      }
    });

    // Address input enter key
    document.addEventListener('keypress', (e) => {
      if (e.target.id === 'address' && e.key === 'Enter') {
        e.preventDefault();
        this.geocodeAddress();
      }
    });

    // Address input change - hide radius dropdown if address is cleared
    document.addEventListener('input', (e) => {
      if (e.target.id === 'address') {
        if (!e.target.value.trim()) {
          // Clear coordinates and hide radius dropdown when address is cleared
          document.getElementById('lat').value = '';
          document.getElementById('lon').value = '';
          this.hideRadiusDropdown();
        }
      }
    });

    // Address input change (for real-time geocoding and autocomplete)
    document.addEventListener('input', (e) => {
      if (e.target.id === 'address') {
        this.debounceGeocode(e.target.value);
        this.debounceAutocomplete(e.target.value);
      }
    });

    // Address input focus (show suggestions)
    document.addEventListener('focus', (e) => {
      if (e.target.id === 'address') {
        this.showQuickPicks();
      }
    });

    // Address input blur (hide suggestions after delay)
    document.addEventListener('blur', (e) => {
      if (e.target.id === 'address') {
        setTimeout(() => {
          this.hideSuggestions();
        }, 200);
      }
    });

    // Keyboard navigation for suggestions
    document.addEventListener('keydown', (e) => {
      if (e.target.id === 'address') {
        this.handleKeyboardNavigation(e);
      }
    });

    // Quick pick buttons
    document.addEventListener('click', (e) => {
      if (e.target.closest('.quick-pick-btn')) {
        e.preventDefault();
        const address = e.target.closest('.quick-pick-btn').dataset.address;
        this.selectQuickPick(address);
      }
    });

    // Use my location button
    document.addEventListener('click', (e) => {
      if (e.target.closest('#useMyLocationBtn')) {
        e.preventDefault();
        this.useMyLocation();
      }
    });

    // Clear location button
    document.addEventListener('click', (e) => {
      if (e.target.closest('#clearLocationBtn')) {
        e.preventDefault();
        this.clearLocation();
      }
    });

    // Change location button
    document.addEventListener('click', (e) => {
      if (e.target.closest('#changeLocationBtn')) {
        e.preventDefault();
        this.changeLocation();
      }
    });
  }

  debounceGeocode(address) {
    // Clear existing timeout
    if (this.geocodeTimeout) {
      clearTimeout(this.geocodeTimeout);
    }

    // Set new timeout for geocoding
    this.geocodeTimeout = setTimeout(() => {
      if (address.trim().length > 3) {
        this.geocodeAddress();
      }
    }, 1000); // 1 second delay
  }

  debounceAutocomplete(address) {
    // Clear existing timeout
    if (this.autocompleteTimeout) {
      clearTimeout(this.autocompleteTimeout);
    }

    // Set new timeout for autocomplete
    this.autocompleteTimeout = setTimeout(() => {
      if (address.trim().length > 2) {
        this.fetchAutocompleteSuggestions(address);
      } else {
        this.hideSuggestions();
      }
    }, 300); // 300ms delay for autocomplete
  }

  async fetchAutocompleteSuggestions(address) {
    try {
      // Use the geocoding API to get suggestions
      const response = await fetch(`/api/search/by-location/?address=${encodeURIComponent(address)}&radius_miles=10&suggestions=true`);
      
      if (response.ok) {
        const data = await response.json();
        if (data.suggestions && data.suggestions.length > 0) {
          this.showAutocompleteSuggestions(data.suggestions);
        } else {
          this.hideSuggestions();
        }
      }
    } catch (error) {
      console.error('Autocomplete error:', error);
      this.hideSuggestions();
    }
  }

  showAutocompleteSuggestions(suggestions) {
    let suggestionsContainer = document.getElementById('autocompleteSuggestions');
    
    if (!suggestionsContainer) {
      suggestionsContainer = document.createElement('div');
      suggestionsContainer.id = 'autocompleteSuggestions';
      suggestionsContainer.className = 'autocomplete-suggestions';
      suggestionsContainer.style.cssText = `
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        background: white;
        border: 1px solid #ddd;
        border-top: none;
        border-radius: 0 0 4px 4px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        z-index: 1000;
        max-height: 200px;
        overflow-y: auto;
      `;
      
      const addressInput = document.getElementById('address');
      const inputGroup = addressInput.closest('.input-group');
      inputGroup.style.position = 'relative';
      inputGroup.appendChild(suggestionsContainer);
    }

    suggestionsContainer.innerHTML = suggestions.map((suggestion, index) => `
      <div class="suggestion-item" data-index="${index}" data-address="${suggestion.address}">
        <div class="suggestion-text">${suggestion.address}</div>
        <div class="suggestion-type">${suggestion.type}</div>
      </div>
    `).join('');

    // Add click handlers for suggestions
    suggestionsContainer.querySelectorAll('.suggestion-item').forEach(item => {
      item.addEventListener('click', () => {
        const address = item.dataset.address;
        document.getElementById('address').value = address;
        this.hideSuggestions();
        this.geocodeAddress();
      });
    });

    suggestionsContainer.style.display = 'block';
  }

  hideSuggestions() {
    const suggestionsContainer = document.getElementById('autocompleteSuggestions');
    if (suggestionsContainer) {
      suggestionsContainer.style.display = 'none';
    }
  }

  showQuickPicks() {
    let quickPicksContainer = document.getElementById('quickPicksContainer');
    
    if (!quickPicksContainer) {
      quickPicksContainer = document.createElement('div');
      quickPicksContainer.id = 'quickPicksContainer';
      quickPicksContainer.className = 'quick-picks-container';
      quickPicksContainer.style.cssText = `
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        background: white;
        border: 1px solid #ddd;
        border-top: none;
        border-radius: 0 0 4px 4px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        z-index: 1000;
        padding: 8px;
      `;
      
      const addressInput = document.getElementById('address');
      const inputGroup = addressInput.closest('.input-group');
      inputGroup.style.position = 'relative';
      inputGroup.appendChild(quickPicksContainer);
    }

    quickPicksContainer.innerHTML = `
      <div class="quick-picks-section">
        <div class="quick-picks-title">Quick Picks:</div>
        <div class="quick-picks-buttons">
          <button type="button" class="btn btn-sm btn-outline-primary quick-pick-btn" data-address="London, KY">
            <i class="fas fa-map-marker-alt me-1"></i>London, KY
          </button>
          <button type="button" class="btn btn-sm btn-outline-primary quick-pick-btn" data-address="Lexington, KY">
            <i class="fas fa-map-marker-alt me-1"></i>Lexington, KY
          </button>
          <button type="button" class="btn btn-sm btn-outline-primary quick-pick-btn" data-address="Louisville, KY">
            <i class="fas fa-map-marker-alt me-1"></i>Louisville, KY
          </button>
          <button type="button" class="btn btn-sm btn-outline-primary quick-pick-btn" data-address="Bowling Green, KY">
            <i class="fas fa-map-marker-alt me-1"></i>Bowling Green, KY
          </button>
        </div>
        <div class="quick-picks-actions mt-2">
          <button type="button" class="btn btn-sm btn-outline-success" id="useMyLocationBtn">
            <i class="fas fa-location-arrow me-1"></i>Use My Location
          </button>
          <button type="button" class="btn btn-sm btn-outline-secondary" id="clearLocationBtn">
            <i class="fas fa-times me-1"></i>Clear Location
          </button>
        </div>
      </div>
    `;

    quickPicksContainer.style.display = 'block';
  }

  selectQuickPick(address) {
    document.getElementById('address').value = address;
    this.hideSuggestions();
    this.geocodeAddress();
  }

  async useMyLocation() {
    if (!navigator.geolocation) {
      this.showLocationFeedback('Geolocation is not supported by your browser.', 'warning');
      return;
    }

    this.showLocationFeedback('Getting your location...', 'info');

    try {
      const position = await new Promise((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject, {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 60000
        });
      });

      const { latitude, longitude } = position.coords;
      
      // Reverse geocode to get address
      const response = await fetch(`/api/search/by-location/?lat=${latitude}&lon=${longitude}&radius_miles=10`);
      
      if (response.ok) {
        const data = await response.json();
        if (data.location && data.location.address) {
          document.getElementById('address').value = data.location.address;
          document.getElementById('lat').value = latitude;
          document.getElementById('lon').value = longitude;
          this.showLocationFeedback(`Location set: ${data.location.address}`, 'success');
          this.hideSuggestions();
          
          // Auto-submit form
          setTimeout(() => {
            document.getElementById('filterForm')?.submit();
          }, 1000);
        }
      }
    } catch (error) {
      console.error('Geolocation error:', error);
      this.showLocationFeedback('Could not get your location. Please enter an address manually.', 'danger');
    }
  }

  clearLocation() {
    document.getElementById('address').value = '';
    document.getElementById('lat').value = '';
    document.getElementById('lon').value = '';
    this.hideSuggestions();
    this.showLocationFeedback('Location cleared.', 'info');
  }

  changeLocation() {
    // Clear current location and focus on address input
    document.getElementById('address').value = '';
    document.getElementById('lat').value = '';
    document.getElementById('lon').value = '';
    
    // Hide location confirmation
    const locationConfirmation = document.querySelector('.location-confirmation');
    if (locationConfirmation) {
      locationConfirmation.style.display = 'none';
    }
    
    // Focus on address input and show quick picks
    const addressInput = document.getElementById('address');
    addressInput.focus();
    this.showQuickPicks();
    
    this.showLocationFeedback('Enter a new location.', 'info');
  }

  handleKeyboardNavigation(event) {
    const suggestionsContainer = document.getElementById('autocompleteSuggestions');
    if (!suggestionsContainer || suggestionsContainer.style.display === 'none') {
      return;
    }

    const suggestions = suggestionsContainer.querySelectorAll('.suggestion-item');
    const currentIndex = parseInt(suggestionsContainer.dataset.selectedIndex || -1);

    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault();
        const nextIndex = currentIndex < suggestions.length - 1 ? currentIndex + 1 : 0;
        this.highlightSuggestion(suggestions, nextIndex);
        break;
      case 'ArrowUp':
        event.preventDefault();
        const prevIndex = currentIndex > 0 ? currentIndex - 1 : suggestions.length - 1;
        this.highlightSuggestion(suggestions, prevIndex);
        break;
      case 'Enter':
        event.preventDefault();
        if (currentIndex >= 0 && suggestions[currentIndex]) {
          const address = suggestions[currentIndex].dataset.address;
          document.getElementById('address').value = address;
          this.hideSuggestions();
          this.geocodeAddress();
        }
        break;
      case 'Escape':
        event.preventDefault();
        this.hideSuggestions();
        break;
    }
  }

  highlightSuggestion(suggestions, index) {
    suggestions.forEach((suggestion, i) => {
      suggestion.classList.toggle('highlighted', i === index);
    });
    const container = document.getElementById('autocompleteSuggestions');
    if (container) {
      container.dataset.selectedIndex = index;
    }
  }

  async geocodeAddress() {
    const addressInput = document.getElementById('address');
    const geocodeBtn = document.getElementById('geocodeBtn');
    const locationFeedback = document.getElementById('locationFeedback');
    const locationMessage = document.getElementById('locationMessage');
    const latInput = document.getElementById('lat');
    const lonInput = document.getElementById('lon');

    const address = addressInput.value.trim();
    
    if (!address) {
      this.showLocationFeedback('Please enter an address or city name.', 'warning');
      return;
    }

    // Show loading state
    this.showLocationFeedback('Geocoding address...', 'info');
    geocodeBtn.disabled = true;
    geocodeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

    try {
      // Use the existing location search API
      const response = await fetch(`/api/search/by-location/?address=${encodeURIComponent(address)}&radius_miles=10`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.location && data.location.coordinates) {
        const [lat, lon] = data.location.coordinates;
        
        // Update hidden coordinate fields
        latInput.value = lat;
        lonInput.value = lon;
        
        // Show radius dropdown since we now have coordinates
        this.showRadiusDropdown();
        
        // Show success message
        this.showLocationFeedback(`Location found: ${data.location.address}`, 'success');
        
        // Auto-submit form if we have coordinates
        setTimeout(() => {
          document.getElementById('filterForm').submit();
        }, 1000);
        
      } else {
        throw new Error('No coordinates found in response');
      }
      
    } catch (error) {
      console.error('Geocoding error:', error);
      this.showLocationFeedback('Could not find that location. Please try a different address or city name.', 'danger');
      
      // Clear coordinates
      latInput.value = '';
      lonInput.value = '';
      
      // Hide radius dropdown since we no longer have coordinates
      this.hideRadiusDropdown();
    } finally {
      // Reset button state
      geocodeBtn.disabled = false;
      geocodeBtn.innerHTML = '<i class="fas fa-map-marker-alt"></i>';
    }
  }

  showRadiusDropdown() {
    const radiusGroup = document.querySelector('.filter-group:has(#radius_miles)');
    const radiusInfo = document.querySelector('.form-text:has(.fa-info-circle)');
    
    if (radiusGroup) {
      radiusGroup.style.display = 'block';
    }
    if (radiusInfo) {
      radiusInfo.style.display = 'none';
    }
  }

  hideRadiusDropdown() {
    const radiusGroup = document.querySelector('.filter-group:has(#radius_miles)');
    const radiusInfo = document.querySelector('.form-text:has(.fa-info-circle)');
    
    if (radiusGroup) {
      radiusGroup.style.display = 'none';
    }
    if (radiusInfo) {
      radiusInfo.style.display = 'block';
    }
  }

  showLocationFeedback(message, type = 'info') {
    const locationFeedback = document.getElementById('locationFeedback');
    const locationMessage = document.getElementById('locationMessage');
    
    if (locationFeedback && locationMessage) {
      locationMessage.textContent = message;
      
      // Update alert class
      const alertDiv = locationFeedback.querySelector('.alert');
      alertDiv.className = `alert alert-${type} alert-sm`;
      
      // Show feedback
      locationFeedback.style.display = 'block';
      
      // Auto-hide after 5 seconds for success/info messages
      if (type === 'success' || type === 'info') {
        setTimeout(() => {
          locationFeedback.style.display = 'none';
        }, 5000);
      }
    }
  }
}

// Initialize location search manager when DOM is loaded
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    new LocationSearchManager();
  });
} else {
  new LocationSearchManager();
}

// Export for potential use in other scripts
window.LocationSearchManager = LocationSearchManager;

// ===== HYBRID FILTER LAYOUT FUNCTIONALITY =====

class HybridFilterManager {
  constructor() {
    this.init();
  }

  init() {
    this.addEventListeners();
    this.updateFilterCount();
    this.checkAndExpandAccordions();
  }

  addEventListeners() {
    // Toggle advanced filters with smooth animation
    const toggleBtn = document.getElementById('toggleAdvancedFilters');
    if (toggleBtn) {
      toggleBtn.addEventListener('click', () => this.toggleAdvancedFilters());
    }

    // Address input change - hide radius dropdown if address is cleared
    const addressInput = document.getElementById('address');
    if (addressInput) {
      addressInput.addEventListener('input', (e) => this.handleAddressChange(e));
    }
  }

  toggleAdvancedFilters() {
    const advancedFilters = document.getElementById('advancedFilters');
    const button = document.getElementById('toggleAdvancedFilters');
    
    if (advancedFilters.style.display === 'none') {
      // Show advanced filters
      advancedFilters.style.display = 'block';
      advancedFilters.style.maxHeight = 'none';
      advancedFilters.classList.add('expand-animation');
      
      button.innerHTML = '<i class="fas fa-chevron-up me-1"></i>Hide Filters <span class="filter-count-badge" id="filterCount">' + this.getActiveFilterCount() + '</span>';
    } else {
      // Hide advanced filters
      advancedFilters.style.maxHeight = '0';
      advancedFilters.classList.remove('expand-animation');
      
      setTimeout(() => {
        advancedFilters.style.display = 'none';
      }, 300);
      
      button.innerHTML = '<i class="fas fa-sliders-h me-1"></i>More Filters <span class="filter-count-badge" id="filterCount">' + this.getActiveFilterCount() + '</span>';
    }
  }



  getColorClass(button) {
    const classes = button.className.split(' ');
    for (const cls of classes) {
      if (cls.startsWith('btn-outline-')) {
        return cls.replace('btn-outline-', '');
      }
    }
    return 'primary';
  }

  handleAddressChange(event) {
    if (!event.target.value.trim()) {
      // Clear coordinates and hide radius dropdown when address is cleared
      const latInput = document.getElementById('lat');
      const lonInput = document.getElementById('lon');
      if (latInput) latInput.value = '';
      if (lonInput) lonInput.value = '';
      this.hideRadiusDropdown();
    }
  }

  showRadiusDropdown() {
    const radiusGroup = document.querySelector('.filter-group:has(#radius_miles)');
    const radiusInfo = document.querySelector('.form-text:has(.fa-info-circle)');
    
    if (radiusGroup) {
      radiusGroup.style.display = 'block';
    }
    if (radiusInfo) {
      radiusInfo.style.display = 'none';
    }
  }

  hideRadiusDropdown() {
    const radiusGroup = document.querySelector('.filter-group:has(#radius_miles)');
    const radiusInfo = document.querySelector('.form-text:has(.fa-info-circle)');
    
    if (radiusGroup) {
      radiusGroup.style.display = 'none';
    }
    if (radiusInfo) {
      radiusInfo.style.display = 'block';
    }
  }

  updateFilterCount() {
    const count = this.getActiveFilterCount();
    const countElement = document.getElementById('filterCount');
    if (countElement) {
      countElement.textContent = count;
    }
  }

  getActiveFilterCount() {
    const activeFilters = document.querySelectorAll('.quick-filter-btn.btn-primary, .quick-filter-btn.btn-danger, .quick-filter-btn.btn-success, .quick-filter-btn.btn-warning, .quick-filter-btn.btn-info, .quick-filter-btn.btn-secondary');
    return activeFilters.length;
  }

  checkAndExpandAccordions() {
    // Check if any filters are active and expand relevant accordions
    const categoryField = document.getElementById('category');
    const serviceTypeField = document.getElementById('service_type');
    
    if (categoryField && categoryField.value || serviceTypeField && serviceTypeField.value) {
      this.expandAccordion('serviceCollapse');
    }
    
    const cityField = document.getElementById('city');
    const stateField = document.getElementById('state');
    const addressField = document.getElementById('address');
    
    if (cityField && cityField.value || stateField && stateField.value || addressField && addressField.value) {
      this.expandAccordion('locationCollapse');
    }
    
    const hour24Field = document.getElementById('24hour');
    const emergencyField = document.getElementById('emergency');
    
    if (hour24Field && hour24Field.value || emergencyField && emergencyField.value) {
      this.expandAccordion('availabilityCollapse');
    }
  }

  expandAccordion(collapseId) {
    const collapseElement = document.getElementById(collapseId);
    if (collapseElement) {
      const bsCollapse = new bootstrap.Collapse(collapseElement, { show: true });
    }
  }
}

// Initialize hybrid filter manager when DOM is loaded
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    new HybridFilterManager();
  });
} else {
  new HybridFilterManager();
}

// Export for potential use in other scripts
window.HybridFilterManager = HybridFilterManager;
