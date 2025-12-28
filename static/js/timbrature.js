document.addEventListener('DOMContentLoaded', function () {
    // Elementi DOM
    const dipendenteContainer = document.getElementById('dipendenti-container');
    const timbraModal = new bootstrap.Modal(document.getElementById('timbraModal'));
    const nomeDipendente = document.getElementById('dipendente-nome');
    const confermaTimbraturaBtn = document.getElementById('conferma-timbratura');
    const timbraToast = new bootstrap.Toast(document.getElementById('timbratoast'));
    const toastMessage = document.getElementById('toast-message');

    // Variabili globali
    let dipendenteSelezionato = null;

    // Carica i dipendenti all'avvio
    caricaDipendenti();

    // Event listener per il pulsante di conferma timbratura
    confermaTimbraturaBtn.addEventListener('click', function () {
        if (!dipendenteSelezionato) return;

        // Richiesta AJAX per registrare la timbratura
        const formData = new FormData();
        formData.append('dipendente_id', dipendenteSelezionato);

        fetch('/timbratura', {
            method: 'POST',
            body: formData
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Chiudi il modal
                    timbraModal.hide();

                    // Mostra il toast di conferma
                    if (toastMessage) toastMessage.textContent = data.message;
                    timbraToast.show();

                    // Ricarica i dipendenti per aggiornare lo stato
                    setTimeout(caricaDipendenti, 500);
                } else {
                    alert('Si è verificato un errore durante la registrazione della timbratura');
                }
            })
            .catch(error => {
                console.error('Errore:', error);
                alert('Si è verificato un errore durante la registrazione della timbratura');
            });
    });

    // Funzione per caricare i dipendenti
    function caricaDipendenti() {
        fetch('/api/stato-dipendenti')
            .then(response => response.json())
            .then(data => {
                renderizzaDipendenti(data);
            })
            .catch(error => {
                console.error('Errore:', error);
                dipendenteContainer.innerHTML = `
                    <div class="col-12 text-center">
                        <div class="alert alert-danger border-0 shadow-sm" role="alert">
                            <i class="fas fa-exclamation-triangle me-2"></i>
                            Si è verificato un errore durante il caricamento dei dipendenti.
                        </div>
                    </div>
                `;
            });
    }

    // Funzione per renderizzare i dipendenti
    function renderizzaDipendenti(dipendenti) {
        // Ordina i dipendenti per cognome, nome
        dipendenti.sort((a, b) => {
            if (a.cognome !== b.cognome) {
                return a.cognome.localeCompare(b.cognome);
            }
            return a.nome.localeCompare(b.nome);
        });

        let html = '';

        if (dipendenti.length === 0) {
            html = `
                <div class="col-12 text-center">
                    <div class="alert alert-info border-0 shadow-sm" role="alert">
                        <i class="fas fa-info-circle me-2"></i>
                        Nessun dipendente registrato nel sistema.
                    </div>
                </div>
            `;
        } else {
            dipendenti.forEach(dip => {
                const isPresente = dip.presente;
                const statusClass = isPresente ? 'bg-success-subtle text-success' : 'bg-light text-muted';
                const statusText = isPresente ? 'In Servizio' : 'Non in Servizio';
                const borderClass = isPresente ? 'border-success' : 'border-0';
                const initial = dip.nome.charAt(0) + dip.cognome.charAt(0);

                // Orario inizio se presente
                const timeInfo = dip.inizio ?
                    `<div class="mt-2 small text-muted"><i class="far fa-clock me-1"></i>Entrata: <strong>${dip.inizio}</strong></div>` :
                    `<div class="mt-2 small text-muted opacity-50"><i class="far fa-clock me-1"></i>--:--</div>`;

                html += `
                    <div class="col-md-6 col-lg-4 col-xl-3">
                        <div class="card h-100 shadow-sm dipendente-card cursor-pointer transition-transform hover-lift ${isPresente ? 'border-start border-4 border-success' : ''}" 
                             data-id="${dip.id}" data-nome="${dip.nome} ${dip.cognome}" style="cursor: pointer;">
                            <div class="card-body text-center p-4">
                                <div class="avatar-circle mb-3 mx-auto d-flex align-items-center justify-content-center fw-bold ${isPresente ? 'bg-success text-white' : 'bg-light text-secondary'}" 
                                     style="width: 64px; height: 64px; border-radius: 50%; font-size: 1.2rem;">
                                    ${initial}
                                </div>
                                <h5 class="card-title fw-bold mb-1 text-dark">${dip.cognome} ${dip.nome}</h5>
                                <div class="badge rounded-pill ${statusClass} mb-2 px-3 py-2 fw-normal">
                                    <i class="fas fa-circle me-1 small" style="font-size: 0.5rem;"></i> ${statusText}
                                </div>
                                ${timeInfo}
                            </div>
                        </div>
                    </div>
                `;
            });
        }

        dipendenteContainer.innerHTML = html;

        // Aggiungi event listeners alle card dei dipendenti
        document.querySelectorAll('.dipendente-card').forEach(card => {
            card.addEventListener('click', function () {
                dipendenteSelezionato = this.dataset.id;
                nomeDipendente.textContent = this.dataset.nome;
                timbraModal.show();
            });
        });
    }
});