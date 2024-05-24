/* eslint-disable unicorn/prevent-abbreviations */
import useGetState from 'api/getState';
import { useAtomValue } from 'jotai';
import { useState } from 'react';
import Autosuggest from 'react-autosuggest';
import Confetti from 'react-confetti';
import { getZoneName } from 'translation/translation';
import { emapleZoneAtom } from 'utils/state/atoms';

// Sample list of possible zone names
// const zoneNames = ['Zone1', 'Zone2', 'Zone3', 'ExampleZone', 'SampleZone'];

export function ZoneGuessInput() {
  const { data } = useGetState();
  const state = data?.data?.datetimes[Object.keys(data?.data.datetimes)[0]];
  const zoneKeys = state ? Object.keys(state.z) : [];
  const zoneNames = state ? zoneKeys.map((zoneKey) => getZoneName(zoneKey)) : [];
  const correctZoneName = getZoneName(useAtomValue(emapleZoneAtom)).toLowerCase();
  const correctZoneKey = useAtomValue(emapleZoneAtom).toLowerCase();
  const [guesses, setGuesses] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [message, setMessage] = useState('');
  const [suggestions, setSuggestions] = useState([]);

  const isCorrect =
    inputValue.toLowerCase() === correctZoneName ||
    inputValue.toLowerCase() === correctZoneKey.toLowerCase();

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

  // Autosuggest functions
  const getSuggestions = (value: any) => {
    const inputValue = value.trim().toLowerCase();
    const inputLength = inputValue.length;

    return inputLength === 0
      ? []
      : zoneNames.filter(
          (zone) => zone.toLowerCase().slice(0, inputLength) === inputValue
        );
  };

  const onSuggestionsFetchRequested = ({ value }: any) => {
    // @ts-ignore
    setSuggestions(getSuggestions(value));
  };

  const onSuggestionsClearRequested = () => {
    setSuggestions([]);
  };

  const onSuggestionSelected = (event: any, { suggestion }: any) => {
    setInputValue(suggestion);
  };

  const inputProps = {
    placeholder: 'Enter your zone guess',
    value: inputValue,
    onChange: (_e: any, { newValue }: any) => setInputValue(newValue),
    onKeyDown: handleKeyDown,
    disabled: guesses.length >= 5,
  };

  return (
    <div className="flex h-[300px] w-[500px]">
      <Autosuggest
        suggestions={suggestions}
        onSuggestionsFetchRequested={onSuggestionsFetchRequested}
        onSuggestionsClearRequested={onSuggestionsClearRequested}
        onSuggestionSelected={onSuggestionSelected}
        getSuggestionValue={(suggestion: any) => suggestion}
        renderSuggestion={(suggestion: any) => <div>{suggestion}</div>}
        inputProps={inputProps}
      />
      <button
        className="mx-5 h-10 rounded border bg-green-200 p-2"
        onClick={handleSubmit}
        disabled={guesses.length >= 5}
      >
        Submit
      </button>
      <p>{message}</p>
      <p>Guesses left: {5 - guesses.length}</p>
      {message === 'Correct!' && <Confetti width={400} height={500} />}
    </div>
  );
}
