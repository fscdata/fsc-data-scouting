function plusOne(elementId) {
    event.preventDefault();
    document.getElementById(elementId).stepUp();
 }
function plusFive(elementId) {
    event.preventDefault();
    document.getElementById(elementId).stepUp(5);
 }
function plusTen(elementId) {
    event.preventDefault();
    document.getElementById(elementId).stepUp(10);
 }
 function minusOne(elementId) {
    event.preventDefault();
    document.getElementById(elementId).stepDown();
 }