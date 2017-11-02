/* Service for storing the main state of the application */

class ApplicationService {

    isLocalHost() {
        return window.location.href.indexOf('electricitymap') == -1;
    }

    isProduction() {
        return !this.isLocalHost();
    }
}

module.exports = new ApplicationService(); // Singleton