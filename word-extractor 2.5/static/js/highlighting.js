document.addEventListener('DOMContentLoaded', function() {
    const sourceText = document.getElementById('source-text');
    const statsTable = document.querySelector('.stats-table');
    
    if (sourceText && statsTable) {
        const originalText = sourceText.textContent;
        let highlightedPositions = [];
        let currentHighlightIndex = -1;

        const navigationContainer = document.createElement('div');
        navigationContainer.classList.add('highlight-navigation');
        navigationContainer.innerHTML = `
            <button id="prev-highlight" class="nav-btn">←</button>
            <span id="highlight-counter">0/0</span>
            <button id="next-highlight" class="nav-btn">→</button>
        `;
        sourceText.parentNode.insertBefore(navigationContainer, sourceText);

        const prevBtn = document.getElementById('prev-highlight');
        const nextBtn = document.getElementById('next-highlight');
        const counterSpan = document.getElementById('highlight-counter');

        function updateNavigationButtons() {
            prevBtn.disabled = currentHighlightIndex <= 0;
            nextBtn.disabled = currentHighlightIndex >= highlightedPositions.length - 1;
            counterSpan.textContent = highlightedPositions.length > 0 
                ? `${currentHighlightIndex + 1}/${highlightedPositions.length}` 
                : '0/0';
        }

        function navigateHighlight(direction) {
            if (direction === 'next' && currentHighlightIndex < highlightedPositions.length - 1) {
                currentHighlightIndex++;
            } else if (direction === 'prev' && currentHighlightIndex > 0) {
                currentHighlightIndex--;
            }

            if (currentHighlightIndex >= 0 && currentHighlightIndex < highlightedPositions.length) {
                const pos = highlightedPositions[currentHighlightIndex];
                const highlightedElement = sourceText.querySelector(
                    `.highlighted:nth-child(${currentHighlightIndex + 1})`
                );
                
                if (highlightedElement) {
                    highlightedElement.scrollIntoView({
                        behavior: 'smooth',
                        block: 'center'
                    });
                }
                updateNavigationButtons();
            }
        }

        prevBtn.addEventListener('click', () => navigateHighlight('prev'));
        nextBtn.addEventListener('click', () => navigateHighlight('next'));

        statsTable.querySelectorAll('tbody tr').forEach(row => {
            row.addEventListener('click', function() {
                statsTable.querySelectorAll('tbody tr').forEach(r => {
                    r.classList.remove('active-row');
                    r.querySelectorAll('.word-form').forEach(form => {
                        form.classList.remove('active-form');
                    });
                });

                this.classList.add('active-row');

                const wordForms = Array.from(this.querySelectorAll('.word-form'))
                    .map(form => {
                        form.classList.add('active-form');
                        return form.getAttribute('data-original');
                    });

                let highlightedText = originalText;
                highlightedPositions = [];
                
                wordForms.forEach(word => {
                    let index = -1;
                    while ((index = originalText.indexOf(word, index + 1)) !== -1) {
                        highlightedPositions.push({
                            start: index,
                            end: index + word.length
                        });
                    }
                });

                highlightedPositions.sort((a, b) => b.start - a.start);
                
                highlightedPositions.forEach(pos => {
                    highlightedText = 
                        highlightedText.slice(0, pos.start) + 
                        `<mark class="highlighted active-highlight">` + 
                        highlightedText.slice(pos.start, pos.end) + 
                        `</mark>` + 
                        highlightedText.slice(pos.end);
                });

                sourceText.innerHTML = highlightedText;

                currentHighlightIndex = highlightedPositions.length > 0 ? 0 : -1;
                updateNavigationButtons();

                const firstHighlight = sourceText.querySelector('.active-highlight');
                if (firstHighlight) {
                    firstHighlight.scrollIntoView({
                        behavior: 'smooth',
                        block: 'center'
                    });
                }
            });
        });
    }
});