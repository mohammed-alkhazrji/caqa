odoo.define('code_backend_theme.SidebarMenu', [], function (require) {
    "use strict";

    // Use event delegation for dynamic App Launcher elements
    $(document).on("click", "#caqaOpenLauncher", function(event){
        event.preventDefault();
        $("body").addClass("caqa-app-launcher-open");
    });

    $(document).on("click", "#caqaCloseLauncher, .caqa-app-launcher-overlay", function(event){
        // Close if click is exactly on the overlay background or close button
        if (event.target.id === 'caqa_app_launcher' || event.currentTarget.id === 'caqaCloseLauncher') {
            event.preventDefault();
            $("body").removeClass("caqa-app-launcher-open");
        }
    });

    // Close launcher when an app is clicked
    $(document).on("click", ".caqa-app-card", function(event){
        $("body").removeClass("caqa-app-launcher-open");
    });

    // Close launcher when pressing Esc
    $(document).on("keydown", function(event) {
        if (event.key === "Escape" && $("body").hasClass("caqa-app-launcher-open")) {
            $("body").removeClass("caqa-app-launcher-open");
        }
    });
});
