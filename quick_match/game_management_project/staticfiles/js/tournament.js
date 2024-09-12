// game_manager/static/js/tournament.js

document.addEventListener('DOMContentLoaded', function() {
    const winnerButtons = document.querySelectorAll('.winner-button');
    
    winnerButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const matchId = this.dataset.matchId;
            const winnerId = this.dataset.playerId;
            const tournamentId = this.dataset.tournamentId;
            
            fetch(`/tournament/${tournamentId}/match/${matchId}/select_winner/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({winner_id: winnerId})
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    if (data.tournament_concluded) {
                        alert(`${data.winner_name} has won the match! The tournament has concluded. The overall winner is ${data.tournament_winner}!`);
                    } else {
                        alert(`${data.winner_name} has won the match!`);
                    }
                    location.reload(); // Reload the page to update the bracket
                } else {
                    alert('Error updating match result. Please try again.');
                }
            });
        });
    });
});

// Helper function to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}