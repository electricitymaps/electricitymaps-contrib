// Send a greeting message to the console for curious people
export function createConsoleGreeting() {
  console.info(
    `· · ·
· ϟ · %cWelcome to Electricity Maps!%c
· · ·
🌱 %cReady to work on fixing climate change full-time?
https://electricitymaps.com/jobs
🐙 Got comments or want to contribute?
https://github.com/electricityMaps/electricitymaps-contrib`,
    'color: green; font-weight: bold',
    'color: inherit',
    'color: #666; font-style: italic'
  );
}
