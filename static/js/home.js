var type = new Typed(".questions",
{
    strings: ["Bored?", "Need a breeze of fresh air in your playlist?", "Searching for something new?"],
    typeSpeed: 100,
    backSpeed: 100,
    backDelay: 3000,
    loop: true
})


var type = new Typed(".genres",
{
    strings: ["pop.", "rap.", "rock.", "reggae.", "jazz.", "party music.", "Mozart's classics."],
    typeSpeed: 100,
    backSpeed: 100,
    backDelay: 1000,
    loop: true
})



let sections = document.querySelectorAll('section');
let navLinks = document.querySelectorAll('header nav a');

window.onscroll = () =>
{
    sections.forEach(sec => {
        let top = window.scrollY;
        let offset = sec.offsetTop - 150;
        let height = sec.offsetHeight;
        let id = sec.getAttribute('id');

        if (top >= offset && top < offset + height) {
            navLinks.forEach(links => {
                links.classList.remove('active');
                document.querySelector('header nav a[href*=' + id + ']').classList.add('active');
             });
        };
    });
}




function showHide() {
    var x = document.getElementById("myInput");
    if (x.type === "password") {
      x.type = "text";
    } else {
      x.type = "password";
    }
  }





  $(document).ready(function() {
    $('#genre-form').on('submit', function(event) {
        event.preventDefault();

        $.ajax({
            type: 'POST',
            url: '/generate_genre_playlist',
            data: $(this).serialize(),
            success: function(response) {
                if (response.includes('http')) {
                    $('#genre-result').html('<p>Playlist created! Listen <a href="' + response + '" target="_blank">here</a></p>');
                    $('#genre-result').css('color', 'rgb(164, 64, 77)');
                } else {
                    $('#genre-result').html('<p>' + response + '</p>');
                    $('#genre-result').css('color', 'red');
                }
            },
            error: function(error) {
                $('#genre-result').html('<p>An error occurred while creating the playlist.</p>');
                $('#genre-result').css('color', 'red');
            }
        });
    });
});