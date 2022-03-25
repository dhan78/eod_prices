const el = document.getElementById('container');

const hiddenDiv = document.getElementById('hidden-div');

el.addEventListener('mouseover', function handleMouseOver() {
  hiddenDiv.style.display = 'block';

});

el.addEventListener('mouseout', function handleMouseOut() {
  hiddenDiv.style.display = 'none';

});

