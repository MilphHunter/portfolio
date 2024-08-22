function scrollToElement(targetPath) {
    var targetElement = document.querySelector(targetPath);
    if (targetElement) {
      targetElement.scrollIntoView({
        behavior: 'smooth'
      });
    }
  }