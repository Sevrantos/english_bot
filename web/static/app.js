document.addEventListener('DOMContentLoaded', async () => {
    const Telegram = window.Telegram.WebApp;
    Telegram.expand();

    const loading = document.getElementById('loading');
    const content = document.getElementById('content');
    const error = document.getElementById('error');
    const scoresContainer = document.getElementById('scores-container');

    try {

        const user = Telegram.initDataUnsafe.user;
        if (!user || !user.id) {
            throw new Error('User not found in Telegram context');
        }

        const response = await fetch(`/students/${user.id}/scores`);
        if (!response.ok) throw new Error('Failed to fetch scores');

        const data = await response.json();

        loading.style.display = 'none';
        content.style.display = 'block';

        renderScores(data);
    } catch (err) {
        loading.style.display = 'none';
        error.style.display = 'block';
        error.textContent = `Error: ${err.message}`;
    }

    function renderScores(data) {
        scoresContainer.innerHTML = data.classes.map(classItem => `
            <div class="class-card">
                <h2 class="class-title">Клас ${classItem.class_number}</h2>
                ${classItem.topics.map(topic => `
                    <div class="topic-card">
                        <h3 class="topic-title">${topic.title}</h3>
                        <div class="lessons-list">
                            ${topic.lessons.map(lesson => `
                                <div class="lesson-item">
                                    <span>${lesson.title}</span>
                                    <span class="score-value">${lesson.score.score}%</span>
                                </div>
                            `).join('')}
                        </div>
                        ${topic.quiz_score ? `
                            <div class="quiz-score">
                                Тест по темі: <span class="score-value">${topic.quiz_score.score}%</span>
                            </div>
                        ` : ''}
                    </div>
                `).join('')}
            </div>
        `).join('');
    }

    Telegram.onEvent('themeChanged', () => {
        document.documentElement.style.setProperty('--tg-theme-bg-color', Telegram.colorScheme.bg_color);
        document.documentElement.style.setProperty('--tg-theme-text-color', Telegram.colorScheme.text_color);
    });
});