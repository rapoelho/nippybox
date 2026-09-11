#!/usr/bin/perl

# obmenu-generator - schema file

=for comment

    item:      add an item inside the menu               {item => ["command", "label", "icon"]},
    cat:       add a category inside the menu             {cat => ["name", "label", "icon"]},
    sep:       horizontal line separator                  {sep => undef}, {sep => "label"},
    pipe:      a pipe menu entry                         {pipe => ["command", "label", "icon"]},
    file:      include the content of an XML file        {file => "/path/to/file.xml"},
    raw:       any XML data supported by Openbox          {raw => q(...)},
    beg:       begin of a category                        {beg => ["name", "icon"]},
    end:       end of a category                          {end => undef},
    obgenmenu: generic menu settings                {obgenmenu => ["label", "icon"]},
    exit:      default "Exit" action                     {exit => ["label", "icon"]},

=cut

# NOTE:
#    * Keys and values are case sensitive. Keep all keys lowercase.
#    * ICON can be a either a direct path to an icon or a valid icon name
#    * Category names are case insensitive. (X-XFCE and x_xfce are equivalent)

require "$ENV{HOME}/.config/obmenu-generator/config.pl";

## Text editor
my $editor = $CONFIG->{editor};

our $SCHEMA = [

    #          COMMAND                 LABEL              ICON
    {item => ['xdg-open .',       'File Manager', 'system-file-manager']},
    {item => ['alacritty',            'Terminal',     'utilities-terminal']},
    {item => ['xdg-open http://', 'Web Browser',  'web-browser']},
    {item => ['rofi-launcher run',            'Run command',  'system-run']},

    {sep => 'Categories'},

    #          NAME            LABEL                ICON
    {cat => ['utility',     'Accessories', 'applications-utilities']},
    {cat => ['development', 'Development', 'applications-development']},
    {cat => ['education',   'Education',   'applications-science']},
    {cat => ['game',        'Games',       'applications-games']},
    {cat => ['graphics',    'Graphics',    'applications-graphics']},
    {cat => ['audiovideo',  'Multimedia',  'applications-multimedia']},
    {cat => ['network',     'Network',     'applications-internet']},
    {cat => ['office',      'Office',      'applications-office']},
    {cat => ['other',       'Other',       'applications-other']},
    {cat => ['settings',    'Settings',    'applications-accessories']},
    {cat => ['system',      'System',      'applications-system']},

    {sep => 'Screen Capture'},
    {pipe => ['nippy-shot --pipe', 'Screenshot', 'gnome-screenshot']},
    {pipe => ['nippy-rec --pipe', 'Record Desktop', 'record-desktop']},
    
    {sep => 'System'},

    {beg => ['Settings', 'applications-engineering']},
		{sep => 'Desktop Settings'},
		{item => ['lxappearance',       'Appearance Settings', 'org.xfce.settings.appearance']},
		{item => ['rofi-wal', 'Change Wallpaper', 'desktop']},
		{pipe => ['nippy-compositor pipe', 'Compositor', 'org.xfce.xfwm4-tweaks']},
		
		{beg => ['Openbox', 'openbox']},
			{item => ['openbox --reconfigure',               'Reconfigure Openbox', 'openbox']},
			{item => ['openbox --restart',               'Restart Openbox', 'openbox']},
			{sep => 'Edit Files'},
			{item => ["$editor ~/.config/openbox/autostart.sh", 'Openbox Autostart',   'text-x-generic']},
			{item => ["$editor ~/.config/openbox/rc.xml",    'Openbox RC',          'text-x-generic']},
			{item => ["$editor ~/.config/openbox/menu.xml",  'Openbox Menu',        'text-x-generic']},
		{end => undef},
		
      # obmenu-generator category
		{beg => ['Obmenu-Generator', 'accessories-text-editor']},
			{item => ["$editor ~/.config/obmenu-generator/schema.pl", 'Menu Schema', 'text-x-generic']},
			{item => ["$editor ~/.config/obmenu-generator/config.pl", 'Menu Config', 'text-x-generic']},

			{sep  => undef},
			{item => ['obmenu-generator -s -c',    'Generate a static menu',             'accessories-text-editor']},
			{item => ['obmenu-generator -s -i -c', 'Generate a static menu with icons',  'accessories-text-editor']},
			
			{sep  => undef},
			{item => ['obmenu-generator -p',       'Generate a dynamic menu',            'accessories-text-editor']},
			{item => ['obmenu-generator -p -i',    'Generate a dynamic menu with icons', 'accessories-text-editor']},
			
			{sep  => undef},
			{item => ['obmenu-generator -d', 'Refresh cache', 'view-refresh']},
		{end => undef},
		
		{sep => 'System Settings'},
		{pipe => ['nippy-randr', 'Display/Monitor', 'display']},
		{item => ['pavucontrol', 'Audio Settings', 'audio-card']},
		#~ {item => ['', 'Power Settings']},
		#~ {item => ['', 'Settings Manager']}, 
    {end => undef},

    {sep => undef},
    {item => ['betterlockscreen --lock', 'Lock', 'system-lock-screen']},
    {item => ['rofi-powermenu', 'Exit', 'application-exit']}
]
