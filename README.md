# Nippybox, um Void com Openbox bem opinativo
Eu estava usando o Archcraft, uma distro Linux com a base que gosto (Arch) e um dos ambientes que eu mais gosto de usar (Openbox) e até que gostei dessa experiência.

Porém, alguns problemas chatos; como a Steam em Flatpak não funcionar e alguns ícones na Plank ficarem duplicados; acabaram me frustrando. Além de ter muitos aplicativos que, pra mim, eram redundantes.

Com essa frustração, mas animado em usar o Openbox e inspirado pelo Omarchy (que é um Arch com Hyprland bem opinativo), decidi pegar a minha configuração do Openbox e fazer um Script para uma instalação do Openbox bastante opinativa, com as aplicações que gosto de usar no Openbox.

Essa configuração havia sido feita inicialmente para o Arch Linux, mas acabou sendo adaptada para o Void Linux.

## O Script de Instalação
O Script de Instalação do Nippybox instala um Openbox configurado a partir de uma instalação do Void Linux feita tanto pelo `void-installer` quanto pelo `chroot`. O script **não deve ser executado como superusuário**, pois a senha do superusuário será pedida quando necessário. 

Os pacotes são instalados com o parâmetro de `-y` para não precisar da confirmação do usuário. Atualmente, o Script instala o XLibre para usar com o Openbox.

### Como executar o Script
Para executar o Script, o melhor seria ter o `git` instalado, com o comando `sudo pacman -Syu git`. Com o git instalado, o Nippybox pode ser instalado com o comando:
```
git clone https://github.com/rapoelho/nippybox.git
cd nippybox
chmod +x install-old.sh
./install-old.sh
```
E com isso, o Nippybox será instalado.

## Pacotes a serem instalados
### Pacotes básicos do Nippybox
O Nippybox é nada mais que uma configuração do Openbox que envolve esses aplicativos:
- **Openbox:** Essa é a base de tudo;
- **Polybar:** Precisava de uma barra que fosse simples e bem configurável, e a Polybar é exatamente isso;
- **Rofi:** É um lançados bastante flexível. É a base de vários dos utilitários que foram implementados;
- **Dunst:** É um gestor de notificações bem flexível;
- **Plank:** O Plank é uma doca simples, bonita e funcional. O que gosto bastante nas minhas configurações;
- **Feh:** Um aplicativo simples para aplicar papéis de parede. É uma das bases do `nippy-colorizer` e do `rofi-wal`;
- **Picom** e **Xcompmgr:** São dois compositores para dar efeitos de sombra e transferência. O Xcompmgr é mais simples e tem o básico para que aplicativos que precisam de um compositor, funcione. E o Picom é mais completo, tendo a possibilidade de ter mais animações;
- **Better Lockscreen:** É uma tela de bloqueio simples, bonita e funcional.

### Dependências do Nippybox
Há outros pacotes que complementam a experiência do Openbox. Seja por facilitarem algumas coisas no ambiente ou por serem base de alguns scripts.
- **Obconf-qt:** A versão Qt do obconf, o utilitário gráfico de configuração do Openbox;
- **obmenu-generator:** Gera o Menu do Openbox. Ou seja, o menu do Openbox não é mais configurado no `menu.xml`;
- **Maim:** Tira capturas de tela. É usado pelo nippy-shot;
- **Playerctl:** Controla Player compatíveis com o MPRIS. É utilizado pelo nippy-keys para o controle de mídia e é a base do rofi-music;
- **FFMPEG:** Um canivete suíço para manipulação de vídeo. É utilizado pelo nippy-rec para gravar a tela;
- **Xclip:** Interage com a Área de Transferência. É usado por alguns scripts;
- **Slop:** Utilizado para fazer uma seleção na tela;
- **XDG-User-Dirs:** É utilizado para gerar as pastas dos usuários;
- **brightnessctl:** É utilizado pelo nippy-keys para o controle do brilho;
- **clipnotify:** É utilizado pelo nippy-clippy.

### Seleção de Aplicativos
Não é só do Openbox e dos Scripts que o Nippybox é formado, mas também de uma seleção de aplicativos que eu selecionei para usar junto com o Openbox que foi montado.
- **Thunar:** O Gerenciador de Arquivos do XFCE, mas que escolhi por ser relativamente completo e sem ter tantas dependências, assim como o Power Manager e o Settings.
- **Viewnior:** Um Visualizador de Imagens simples. E é isso.
- **Alacritty:** Um Terminal acelerado por GPU e que gostei por ser minimalista por padrão;
- **Geany:** Um editor de texto leve e poderoso. Pode servir como uma simples IDE para projetos de programação;
- **MPV:** Um Player Multimídia bem competente e compatível com o MPRIS. Ele é bem flexível;
- **Xreader:** Um Leitor de PDF bem leve. Apenas isso;
- **Galculator:** Nada mais do que um aplicativo de calculadora. Só isso mesmo;
- **Firefox:** Apenas o Navegador que adoro usar. Para mim, é um navegador bem competente, apesar da Mozilla;
- **Xarchiver:** Um compactador de arquivos que escolhi por ser leve;
- **Pavucontrol:** Mais um daqueles programas para controlar alguma coisa. No caso, o Pavucontrol controla os dispositivos relacionados ao Áudio;

## Scripts
- `nippy-colorizer`: É uma das bases do Nippybox. Esse script utiliza um motor próprio feito em Python para extrair a paleta de cores do Wallpaper escolhido e aplica no Rofi, Polybar, Dunst e no tema do Openbox;
- `nippy-keys`: É um Script que controla o volume do áudio, o brilho da tela e os Players compatíveis com o MPRIS, com atalhos de teclados (configurados no arquivo rc.xml do Openbox) ou por comandos. Originalmente eram dois scripts separados no Archcraft (um para Brilho e outro para Volume), mas que mesclei em apenas um único script, adicionando o suporte ao MPRIS;
- `nippy-rec`: Um gravador de tela bem simples que utiliza o FFMPEG para gravar a tela. Pode ser usado como um Pipemenu do Openbox.
- `nippy-shot`: Tira capturas de tela usando o Maim. Pode ser usado como um Pipemenu do Openbox.
- `nippy-sysinfo`: Exibe informações do sistema. Era um Pipemenu do Archcraft, mas que acabei transformando num Fetch bem simples;
- `nippy-wal`: Aplica papeis de parede no Desktop ou na tela de bloqueio. Inicialmente era um Script do Archcraft, mas adicionei o suporte ao nippy-colorizer;
- `nippy-redshift`: Um Script que gerencia o Redshift. Ele detecta a localização e inicia o Redshift com essa localização.
- `nippy-compositor`: Um Script para gerenciar o Compositor. Como o Nippybox vem com dois compositores e apenas um pode ser usado por vez, o `nippy-compositor` existe para ter uma forma de alternar entre o **picom** (padrão) e o **xcompmgr** (fallback).
- `nippy-clippy`: É um gerenciador de área de transferência. Apenas isso. Anteriormente era um Script em Bash, de autoria de [Andrea Fortuna](https://andreafortuna.org/2024/08/04/a-minimalist-approach-to-clipboard-management-in-linux-crafting-a-custom-solution), mas que refiz em Python. Esse Script também executa com o Rofi.
- `nippy-roar`: Um Rofi com uma lista dos outros Rofi que vem com o Nippybox. Nada mais que isso.
- `nippy-settings-daemon`: Um Daemon de Configurações. Foi feito para substituir as partes do XFCE que estavam presentes no sistema.
- `rofi-launcher`: Apenas um Script para exibir o Launcher, o Runner e a Lista de Atalhos com um comando menor
- `rofi-music`: Controla Players compatíveis com o MPRIS. Um player de cada vez. Era um dos scripts do Archcraft, mas o do Archcraft controlava somente o MPD.
- `rofi-powermenu`: Um menu de sessão. É isso.
- `rofi-wifi`: Uma interface para o nm-cli. É um script que foi feito por [Eric Murphy](https://github.com/ericmurphyxyz/rofi-wifi-menu), e que coloquei no Nippybox por ser simples.
- `rofi-emoji`: Um seletor de emojis e que lembra quais foram utilizados anteriormente. Foi feito por [Marty Oehme](https://github.com/marty-oehme/bemoji).
- `rofi-wal`: Um seletor de Papel de Parede. Ele exibe apenas o nome dos arquivos dos Wallpapers e aplica eles usando o nippy-colorizer.

## Problemas conhecidos
- O `nippy-colorizer` pode falhar em alguns Wallpapers;
- Em alguns computadores, o controle de brilho pode funcionar de forma errática;
- Pode haver problemas de conexão com Fones Bluetooth quando o sistema volta da suspensão.

## TODO
- Criar um Daemon de Energia para cuidar das coisas que o Sistema não cuida nativamente
- Fazer o Betterlockscreen entrar em funcionamento quando o computador entra em hibernação
- Refazer todo o Script de Instalação, adaptando ele totalmente para o Void Linux.
