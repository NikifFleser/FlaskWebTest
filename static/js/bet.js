document.addEventListener('DOMContentLoaded', (event) => {
    const inputs = document.querySelectorAll('.goal-input');

    inputs.forEach(input => {
        input.addEventListener('change', (event) => {
            const matchId = event.target.getAttribute('data-match-id');
            const team = event.target.getAttribute('data-team');
            const goals = event.target.value;

            // Make an AJAX request to update the bet
            fetch('/update_bet', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken  // Use the global CSRF token variable
                },
                body: JSON.stringify({
                    match_id: matchId,
                    team: team,
                    goals: goals
                })
            })
            .then(response => response.json())
              .then(data => {
                if (data.status === 'success') {
                    console.log('Bet updated successfully:', data);
                } else {
                    window.location.href = '/bet_route'; // Redirect to the desired route on failure
                }
            })
              .catch((error) => {
                  console.error('Error:', error);
              });
        });
    });
});