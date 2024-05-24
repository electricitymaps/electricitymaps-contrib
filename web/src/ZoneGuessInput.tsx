/* eslint-disable unicorn/prevent-abbreviations */
import { useAtomValue } from 'jotai';
import { useState } from 'react';
import Confetti from 'react-confetti';
import { getZoneName } from 'translation/translation';
import { emapleZoneAtom } from 'utils/state/atoms';

export function ZoneGuessInput() {
  const correctZoneName = getZoneName(useAtomValue(emapleZoneAtom)).toLowerCase();
  const correctZoneKey = useAtomValue(emapleZoneAtom).toLowerCase();
  const [guesses, setGuesses] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [message, setMessage] = useState('');
  const isCorrect =
    inputValue.toLocaleLowerCase() === correctZoneName ||
    inputValue === correctZoneKey.toLowerCase();
  const handleSubmit = () => {
    if (guesses.length >= 5) {
      setMessage('You have no guesses left.');
      return;
    }

    const newGuesses = [...guesses, inputValue];

    // @ts-ignore
    setGuesses(newGuesses);

    if (isCorrect) {
      setMessage('Correct!');
    } else if (newGuesses.length >= 5) {
      setMessage(`Out of guesses! The correct zone name was ${correctZoneName}.`);
    } else {
      setMessage('Incorrect, try again.');
    }

    setInputValue('');
  };

  const handleKeyDown = (e: any) => {
    if (e.key === 'Enter') {
      handleSubmit();
    }
  };

  return (
    <div className="w-[400px]">
      <input
        type="text"
        placeholder="Enter your zone guess"
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={guesses.length >= 5}
      />
      <button
        className="m-5 self-center rounded border bg-green-200 p-2"
        onClick={handleSubmit}
        disabled={guesses.length >= 5}
      >
        Submit
      </button>
      <p>{message}</p>
      <p>Guesses left: {5 - guesses.length}</p>
      {message == 'Correct!' && <Confetti width={400} height={500} />}
    </div>
  );
}
