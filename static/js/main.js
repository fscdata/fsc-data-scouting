function increment(elementId) {
    event.preventDefault();
    document.getElementById(elementId).stepUp();
 }
 function decrement(elementId) {
    event.preventDefault();
    document.getElementById(elementId).stepDown();
 }