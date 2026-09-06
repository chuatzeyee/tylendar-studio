export const PAGES = [
  { id: 'landscape', name: 'Ink landscape', zh: '山水', group: 'Nature', title: 'A little room\nto wander.', description: 'Date-seeded mountains, quiet water, and a new horizon each day.', detail: 'A new ink landscape each day' },
  { id: 'almanac', name: 'Daily almanac', zh: '黃曆', group: 'Daily', title: 'Every day,\na fresh page.', description: 'The Gregorian and lunar calendars, seasonal markers, and the rhythm of the everyday.', detail: 'Day and evening almanac editions' },
  { id: 'poem', name: 'A daily poem', zh: '詩箋', group: 'Daily', title: 'Make space\nfor a few words.', description: 'A Tang poem from a collection of 135, with an English reading close at hand.', detail: 'A daily reading from 135 Tang poems' },
  { id: 'character', name: 'One character', zh: '一字', group: 'Daily', title: 'One character.\nA whole world.', description: 'A generous study of a Chinese character, its meaning, and the words it becomes.', detail: 'Pinyin, meaning, and compounds' },
  { id: 'flora', name: 'Seasonal flora', zh: '四君子', group: 'Nature', title: 'Let the season\ncome inside.', description: 'Plum, orchid, bamboo, and chrysanthemum, drawn afresh as the year unfolds.', detail: 'The Four Gentlemen of ink painting' },
  { id: 'weather', name: 'Island weather', zh: '天氣', group: 'Daily', title: 'A feeling\nfor the day.', description: 'Singapore’s outlook, temperatures, air quality, and the chance of rain.', detail: 'Singapore weather at render time' },
  { id: 'month', name: 'The month', zh: '月曆', group: 'Calendar', title: 'A wider view\nof what’s ahead.', description: 'A considered month calendar with lunar dates, Singapore holidays, and calendar event markers.', detail: 'Lunar dates and public holidays' },
  { id: 'year', name: 'Year in progress', zh: '歲時', group: 'Calendar', title: 'Watch a year\nbecome a life.', description: 'One square for every day. A quiet record of time passed and time still to come.', detail: 'A year of holidays and milestones' },
  { id: 'photo', name: 'Your photographs', zh: '相片', group: 'Personal', title: 'Keep something\nclose to you.', description: 'A daily photograph, translated into the four colors of e-paper and given room to breathe.', detail: 'Your photographs in four ink colors' },
  { id: 'joke', name: 'Local vocabulary', zh: '俚語', group: 'Personal', title: 'A small dose\nof local color.', description: 'A playful dictionary of Singlish profanity, with polite puns and everyday examples.', detail: 'Singlish humor with strong language' },
];
export const GROUPS = ['All prints', 'Daily', 'Nature', 'Calendar', 'Personal'];
export const OPTIONS = {
  landscape: [{ key: 'landscape_scenery', label: 'The scenery', values: ['lake', 'gorge', 'islands', 'night'], names: ['Quiet lake', 'Mountain gorge', 'Islands', 'Night sky'] }],
  poem: [{ key: 'poem_lang', label: 'On the print', values: ['cn', 'en'], names: ['Chinese', 'English'] }],
  month: [{ key: 'month_week_start', label: 'Week begins', values: ['monday', 'sunday'], names: ['Monday', 'Sunday'] }],
  year: [
    { key: 'year_lang', label: 'Language', values: ['bilingual', 'en', 'cn'], names: ['Bilingual', 'English', 'Chinese'] },
    { key: 'year_footer', label: 'At the foot of the page', values: ['holidays', 'event', 'weather'], names: ['Next holiday', 'Calendar event', 'Weather'] },
  ],
  flora: [{ key: 'flora_plant', label: 'The plant', values: ['season', 'plum', 'orchid', 'bamboo', 'chrysanthemum'], names: ['Follow the season', 'Plum blossom', 'Orchid', 'Bamboo', 'Chrysanthemum'] }],
  joke: [{ key: 'joke_word', label: 'The word', values: ['daily', 'jibai', 'kanina', 'lanjiao', 'nabei', 'jiaksai', 'sibei', 'walao', 'siao'], names: ['Daily rotation', 'Ji bai', 'Kan ni na', 'Lan jiao', 'Na beh', 'Jiak sai', 'Si beh', 'Wa lao', 'Siao'] }],
};
export const DEFAULTS = { page: 'landscape', mode: 'auto', hotspot: 'Tylendar' };
export const pageFor = id => PAGES.find(p => p.id === id) || PAGES[0];
