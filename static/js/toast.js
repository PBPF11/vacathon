window.showToast = function(title, message, type = 'normal', duration = 3000) {
    const toastComponent = document.getElementById('toast-component');
    const toastIcon = document.getElementById('toast-icon');
    const toastTitle = document.getElementById('toast-title');
    const toastMessage = document.getElementById('toast-message');
    
    if (!toastComponent) return;

    const typeClasses = [
        'bg-red-50', 'border-red-500', 
        'bg-green-50', 'border-green-500', 
        'bg-white', 'border-gray-300',
        'text-red-600', 'text-green-600', 'text-gray-800'
    ];

    toastComponent.classList.remove(...typeClasses);
    toastIcon.className = 'text-2xl';

    let iconClass = '';
    
    if (type === 'success') {
        toastComponent.classList.add('bg-green-50', 'border-green-500');
        toastTitle.classList.remove('text-gray-800', 'text-red-600');
        toastTitle.classList.add('text-green-600'); 
        iconClass = 'fas fa-check-circle text-green-600'; 

    } else if (type === 'error') {
        toastComponent.classList.add('bg-red-50', 'border-red-500');
        toastTitle.classList.remove('text-gray-800', 'text-green-600');
        toastTitle.classList.add('text-red-600');
        iconClass = 'fas fa-times-circle text-red-600';

    } else {
        toastComponent.classList.add('bg-white', 'border-gray-300');
        toastTitle.classList.remove('text-red-600', 'text-green-600');
        toastTitle.classList.add('text-gray-800');
        iconClass = 'fas fa-info-circle text-gray-500'; 
    }

    toastComponent.style.border = `1px solid ${type === 'success' ? '#22c55e' : (type === 'error' ? '#ef4444' : '#d1d5db')}`;

    toastTitle.textContent = title;
    toastMessage.textContent = message;

    toastIcon.classList.add(...iconClass.split(' ')); 

    setTimeout(() => {
        toastComponent.classList.remove('opacity-0', 'translate-y-64');
        toastComponent.classList.add('opacity-100', 'translate-y-0');
    }, 50);
    
    setTimeout(() => {
        toastComponent.classList.remove('opacity-100', 'translate-y-0');
        toastComponent.classList.add('opacity-0', 'translate-y-64');
    }, duration);
}