/**
 * Unit-Tests für Spracherkennung
 * Ausführen mit: node test-language-detection.js
 */

const franc = require('franc');

// Test-Fälle
const testCases = [
    // Englisch
    { text: "Hello how are you today?", expected: "eng" },
    { text: "Hello, how are you doing today?", expected: "eng" },
    { text: "The quick brown fox jumps over the lazy dog", expected: "eng" },
    { text: "I need to recalibrate my system", expected: "eng" },
    { text: "Good morning, how can I help you?", expected: "eng" },
    { text: "This is a test of the English language", expected: "eng" },
    
    // Deutsch
    { text: "Hallo wie geht es dir?", expected: "deu" },
    { text: "Guten Morgen, wie kann ich Ihnen helfen?", expected: "deu" },
    { text: "Ich möchte etwas trinken", expected: "deu" },
    { text: "Das ist ein Test der deutschen Sprache", expected: "deu" },
    { text: "Während ich tippe, wird die Sprache erkannt", expected: "deu" },
    
    // Französisch
    { text: "Bonjour comment allez vous?", expected: "fra" },
    { text: "Je voudrais un café s'il vous plaît", expected: "fra" },
    { text: "C'est un test de la langue française", expected: "fra" },
    
    // Spanisch
    { text: "Hola como estas hoy?", expected: "spa" },
    { text: "Buenos días, cómo puedo ayudarle?", expected: "spa" },
    { text: "Esta es una prueba del idioma español", expected: "spa" },
];

const allowedLanguages = ['deu', 'eng', 'spa', 'fra'];

console.log("=== Spracherkennung Unit-Tests ===\n");

let passed = 0;
let failed = 0;

testCases.forEach((tc, index) => {
    const detected = franc(tc.text, { minLength: 3, only: allowedLanguages });
    const success = detected === tc.expected;
    
    if (success) {
        passed++;
        console.log(`✅ Test ${index + 1}: "${tc.text.substring(0, 40)}..." → ${detected}`);
    } else {
        failed++;
        console.log(`❌ Test ${index + 1}: "${tc.text.substring(0, 40)}..."`);
        console.log(`   Erwartet: ${tc.expected}, Erkannt: ${detected}`);
    }
});

console.log(`\n=== Ergebnis: ${passed}/${testCases.length} bestanden, ${failed} fehlgeschlagen ===`);

// Test mit längeren Texten
console.log("\n=== Test mit längeren Texten ===\n");

const longerTests = [
    { 
        text: "Hello, how are you? I hope you are having a wonderful day. The weather is beautiful today.", 
        expected: "eng" 
    },
    { 
        text: "Hallo, wie geht es dir? Ich hoffe, du hast einen wunderbaren Tag. Das Wetter ist heute schön.", 
        expected: "deu" 
    },
];

longerTests.forEach((tc, index) => {
    const detected = franc(tc.text, { minLength: 3, only: allowedLanguages });
    const success = detected === tc.expected;
    
    if (success) {
        console.log(`✅ Langer Test ${index + 1}: ${detected} (erwartet: ${tc.expected})`);
    } else {
        console.log(`❌ Langer Test ${index + 1}: ${detected} (erwartet: ${tc.expected})`);
        console.log(`   Text: "${tc.text}"`);
    }
});
