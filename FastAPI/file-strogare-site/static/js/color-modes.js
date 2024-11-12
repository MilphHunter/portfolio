(() => {
  'use strict'

  // Gets the stored theme from localStorage
  const getStoredTheme = () => localStorage.getItem('theme')

  // Saves the theme in localStorage
  const setStoredTheme = theme => localStorage.setItem('theme', theme)

  // Determines the preferred theme: returns the stored theme or sets it
  // based on system settings (dark or light theme)
  const getPreferredTheme = () => {
    const storedTheme = getStoredTheme()
    if (storedTheme) {
      return storedTheme
    }

    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  }

  // Sets the theme by adding the 'data-bs-theme' attribute to the <html> element.
  // If 'auto' theme is set, it checks system settings and applies the appropriate one.
  const setTheme = theme => {
    if (theme === 'auto') {
      document.documentElement.setAttribute('data-bs-theme', (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'))
    } else {
      document.documentElement.setAttribute('data-bs-theme', theme)
    }
  }

  // Sets the theme on page load based on preferences
  setTheme(getPreferredTheme())

  // Displays the active theme on the theme switcher.
  // Updates the icon and text based on the current theme.
  const showActiveTheme = (theme, focus = false) => {
    const themeSwitcher = document.querySelector('#bd-theme')

    // Checks if the theme switcher exists
    if (!themeSwitcher) {
      return
    }

    const themeSwitcherText = document.querySelector('#bd-theme-text')
    const activeThemeIcon = document.querySelector('.theme-icon-active use')
    const btnToActive = document.querySelector(`[data-bs-theme-value="${theme}"]`)
    const svgOfActiveBtn = btnToActive.querySelector('svg use').getAttribute('href')

    // Resets the active state on all theme switcher buttons
    document.querySelectorAll('[data-bs-theme-value]').forEach(element => {
      element.classList.remove('active')
      element.setAttribute('aria-pressed', 'false')
    })

    // Sets the active state on the button for the current theme
    btnToActive.classList.add('active')
    btnToActive.setAttribute('aria-pressed', 'true')
    activeThemeIcon.setAttribute('href', svgOfActiveBtn)

    // Updates the text to describe the theme switcher with the current theme
    const themeSwitcherLabel = `${themeSwitcherText.textContent} (${btnToActive.dataset.bsThemeValue})`
    themeSwitcher.setAttribute('aria-label', themeSwitcherLabel)

    // Sets focus on the theme switcher if the focus parameter is true
    if (focus) {
      themeSwitcher.focus()
    }
  }

  // Automatically changes the theme when system settings change (light/dark)
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    const storedTheme = getStoredTheme()
    if (storedTheme !== 'light' && storedTheme !== 'dark') {
      setTheme(getPreferredTheme())
    }
  })

  // Runs when the DOM is fully loaded
  window.addEventListener('DOMContentLoaded', () => {
    // Displays the active theme on load
    showActiveTheme(getPreferredTheme())

    // Adds click event listeners to all theme toggle buttons
    document.querySelectorAll('[data-bs-theme-value]')
      .forEach(toggle => {
        toggle.addEventListener('click', () => {
          const theme = toggle.getAttribute('data-bs-theme-value')
          setStoredTheme(theme) // Saves the selected theme
          setTheme(theme)       // Applies the selected theme
          showActiveTheme(theme, true) // Displays the active theme on the switcher
        })
      })
  })
})()

// Function to change the icon color on hover
function changeIconColor(button, color) {
  const icon = button.querySelector('.auth-icon');
  if (icon) {
    icon.style.filter = ``;
    icon.style.fill = color;
  }
}

// Function to reset the icon color when hover is removed
function resetIconColor(button) {
  const icon = button.querySelector('.auth-icon');
  if (icon) {
    icon.style.filter = '';
    icon.style.fill = '';
  }
}

