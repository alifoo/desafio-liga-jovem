/**
 * Icon Manager - Centraliza o gerenciamento de ícones para o projeto ClassDocs
 */

class IconManager {
    constructor() {
        this.iconMap = {
            // Navegação
            'home': 'home',
            'teacher': 'graduation-cap',
            'student': 'user',
            'analytics': 'bar-chart-3',
            'bot': 'bot',
            'reports': 'file-text',
            'documents': 'folder',
            
            // Interface
            'menu': 'menu',
            'send': 'send',
            'upload': 'upload',
            'download': 'download',
            'delete': 'trash-2',
            'edit': 'edit-2',
            'search': 'search',
            'settings': 'settings',
            'close': 'x',
            'check': 'check',
            'plus': 'plus',
            'minus': 'minus',
            
            // Analytics
            'chart': 'bar-chart-3',
            'pie-chart': 'pie-chart',
            'trending-up': 'trending-up',
            'trending-down': 'trending-down',
            'users': 'users',
            'clock': 'clock',
            'calendar': 'calendar',
            
            // Status
            'success': 'check-circle',
            'error': 'x-circle',
            'warning': 'alert-triangle',
            'info': 'info'
        };
    }

    /**
     * Aplica ícones automaticamente baseado em classes ou atributos
     */
    applyIcons() {
        // Aplicar ícones de navegação
        this.applyNavigationIcons();
        
        // Aplicar ícones de interface
        this.applyInterfaceIcons();
        
        // Inicializar Lucide
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }

    /**
     * Aplica ícones de navegação automaticamente
     */
    applyNavigationIcons() {
        const navItems = document.querySelectorAll('.nav-item');
        
        navItems.forEach(item => {
            const href = item.getAttribute('href');
            const iconElement = item.querySelector('.nav-item-icon');
            
            if (iconElement && !iconElement.hasAttribute('data-lucide')) {
                let iconName = '';
                
                if (href === '/' || href === '/index') {
                    iconName = this.iconMap.home;
                } else if (href === '/teacher' || href.includes('teacher')) {
                    iconName = this.iconMap.teacher;
                } else if (href === '/student' || href.includes('student')) {
                    iconName = this.iconMap.student;
                } else if (href === '/analytics' || href.includes('analytics')) {
                    iconName = this.iconMap.analytics;
                } else if (item.textContent.includes('Tutor IA')) {
                    iconName = this.iconMap.bot;
                } else if (item.textContent.includes('Relatório')) {
                    iconName = this.iconMap.reports;
                } else if (item.textContent.includes('Documento')) {
                    iconName = this.iconMap.documents;
                }
                
                if (iconName) {
                    iconElement.setAttribute('data-lucide', iconName);
                    iconElement.tagName = 'i';
                }
            }
        });
    }

    /**
     * Aplica ícones de interface automaticamente
     */
    applyInterfaceIcons() {
        // Botão de menu mobile
        const menuButtons = document.querySelectorAll('.mobile-menu-toggle');
        menuButtons.forEach(btn => {
            if (!btn.querySelector('[data-lucide]')) {
                btn.innerHTML = '<i data-lucide="menu"></i>';
            }
        });

        // Botões de send
        const sendButtons = document.querySelectorAll('#sendButton, .send-button');
        sendButtons.forEach(btn => {
            const svg = btn.querySelector('svg.send-icon');
            if (svg) {
                svg.outerHTML = '<i data-lucide="send"></i>';
            }
        });

        // Ícones de arquivo
        const fileIcons = document.querySelectorAll('.file-icon');
        fileIcons.forEach(icon => {
            if (!icon.hasAttribute('data-lucide') && icon.textContent.trim() === '') {
                const parent = icon.closest('.document-item, .metric-card');
                if (parent) {
                    const text = parent.textContent.toLowerCase();
                    if (text.includes('professor') || text.includes('teacher')) {
                        icon.setAttribute('data-lucide', this.iconMap.teacher);
                    } else if (text.includes('estudante') || text.includes('student')) {
                        icon.setAttribute('data-lucide', this.iconMap.student);
                    } else if (text.includes('analytics') || text.includes('métricas')) {
                        icon.setAttribute('data-lucide', this.iconMap.analytics);
                    } else {
                        icon.setAttribute('data-lucide', this.iconMap.documents);
                    }
                }
            }
        });

        // Ícones de métricas
        const metricIcons = document.querySelectorAll('.metric-icon');
        metricIcons.forEach(icon => {
            if (!icon.hasAttribute('data-lucide') && icon.textContent.trim() === '') {
                const parent = icon.closest('.metric-card');
                if (parent) {
                    const text = parent.textContent.toLowerCase();
                    if (text.includes('pergunta') || text.includes('questão')) {
                        icon.setAttribute('data-lucide', 'message-circle');
                    } else if (text.includes('estudante') || text.includes('usuário')) {
                        icon.setAttribute('data-lucide', 'users');
                    } else if (text.includes('disciplina') || text.includes('matéria')) {
                        icon.setAttribute('data-lucide', 'book');
                    } else if (text.includes('tempo') || text.includes('resposta')) {
                        icon.setAttribute('data-lucide', 'clock');
                    } else {
                        icon.setAttribute('data-lucide', 'bar-chart-3');
                    }
                }
            }
        });
    }

    /**
     * Adiciona um ícone específico a um elemento
     */
    addIcon(element, iconName) {
        if (this.iconMap[iconName]) {
            element.setAttribute('data-lucide', this.iconMap[iconName]);
            if (typeof lucide !== 'undefined') {
                lucide.createIcons();
            }
        }
    }

    /**
     * Inicializa o gerenciador de ícones
     */
    static init() {
        const manager = new IconManager();
        
        // Aguardar o DOM carregar
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                manager.applyIcons();
            });
        } else {
            manager.applyIcons();
        }
        
        return manager;
    }
}

// Inicializar automaticamente
IconManager.init();

// Exportar para uso global
window.IconManager = IconManager;
