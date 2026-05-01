// Função para alternar a visualização entre cards e lista
function toggleView(viewType) {
    const gestantesContainer = document.getElementById('gestantesContainer');
    
    // Se a visualização for 'cards', aplique as classes corretas
    if(viewType === 'cards') {
        gestantesContainer.classList.remove('list-view');
        gestantesContainer.classList.add('card-view');
        document.getElementById('toggleCards').classList.add('active');
        document.getElementById('toggleList').classList.remove('active');
    } else { // Se a visualização for 'lista', aplique as classes corretas
        gestantesContainer.classList.remove('card-view');
        gestantesContainer.classList.add('list-view');
        document.getElementById('toggleCards').classList.remove('active');
        document.getElementById('toggleList').classList.add('active');
    }
}

// Definir o padrão de exibição ao carregar a página
window.onload = function() {
    toggleView('cards'); // Carregar a visualização em cards por padrão
};
