document.addEventListener('DOMContentLoaded', () => {
  // Toggle sidebar for responsive screens
  const sidebarCollapse = document.getElementById('sidebarCollapse');
  const sidebar = document.getElementById('sidebar');
  if (sidebarCollapse && sidebar) {
    sidebarCollapse.addEventListener('click', () => {
      sidebar.classList.toggle('active');
    });
  }

  // Dark Mode Toggle Logic
  const themeToggle = document.getElementById('theme-toggle');
  const currentTheme = localStorage.getItem('theme');
  
  if (currentTheme === 'dark') {
    document.body.classList.add('dark-theme');
    if (themeToggle) {
      themeToggle.innerHTML = '<i class="bi bi-sun-fill"></i>';
    }
  } else {
    document.body.classList.remove('dark-theme');
    if (themeToggle) {
      themeToggle.innerHTML = '<i class="bi bi-moon-fill"></i>';
    }
  }

  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      document.body.classList.toggle('dark-theme');
      let theme = 'light';
      if (document.body.classList.contains('dark-theme')) {
        theme = 'dark';
        themeToggle.innerHTML = '<i class="bi bi-sun-fill"></i>';
      } else {
        themeToggle.innerHTML = '<i class="bi bi-moon-fill"></i>';
      }
      localStorage.setItem('theme', theme);
      // Let dashboard charts know to redraw if theme changes
      window.dispatchEvent(new CustomEvent('themeChanged', { detail: theme }));
    });
  }

  // Automatically fade out message alerts after 5 seconds
  const messageAlerts = document.querySelectorAll('.alert-dismissible');
  messageAlerts.forEach(alert => {
    setTimeout(() => {
      // Use Bootstrap's alert class method to close
      if (typeof bootstrap !== 'undefined' && bootstrap.Alert) {
        const bsAlert = bootstrap.Alert.getInstance(alert) || new bootstrap.Alert(alert);
        bsAlert.close();
      } else {
        alert.style.transition = 'opacity 0.5s';
        alert.style.opacity = '0';
        setTimeout(() => alert.remove(), 500);
      }
    }, 5000);
  });
});
