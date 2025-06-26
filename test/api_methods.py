   def set_api_enhancement(self, enabled):
        """Enable or disable external API enhancement"""
        self.enable_api_enhancement = enabled and API_AVAILABLE
        if enabled and not API_AVAILABLE:
            print("Warning: API enhancement requested but dependencies not available")

    def get_api_status(self):
        """Get status of API availability"""
        return {
            'available': API_AVAILABLE,
            'enabled': self.enable_api_enhancement,
            'manager_ready': self.api_manager is not None
        }
