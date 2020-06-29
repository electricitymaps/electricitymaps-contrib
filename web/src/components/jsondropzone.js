import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { store } from '../store';

const JSONDropzone = (handleJSONLoad) => {
  const defaultHandleJSONLoad = (jsonLoad) => {
    const payload = jsonLoad;
    payload.exchanges = payload.exchanges ? payload.exchanges : {};
    store.dispatch({ type: 'GRID_DATA_FETCH_REQUESTED' });
    store.dispatch({ type: 'GRID_DATA_FETCH_SUCCEEDED', payload });
  };
  let JSONLoader;
  if (Object.keys(handleJSONLoad).length === 0 && handleJSONLoad.constructor === Object) {
    JSONLoader = defaultHandleJSONLoad;
  } else {
    JSONLoader = handleJSONLoad;
  }

  const onDrop = useCallback((acceptedFiles) => {
    acceptedFiles.forEach((file) => {
      const reader = new FileReader();

      reader.onabort = () => console.log('file reading was aborted');
      reader.onerror = () => console.log('file reading has failed');
      reader.onload = () => {
      // Do whatever you want with the file contents
        const jsonLoad = JSON.parse(reader.result);
        JSONLoader(jsonLoad);
      };
      reader.readAsText(file);
    });
  }, []);
  const { getRootProps, getInputProps } = useDropzone({ onDrop });
  return (
    <div {...getRootProps()}>
      <input {...getInputProps()} />
      <span role="img" aria-label="json_dropzone">📜</span>
    </div>
  );
};

export default JSONDropzone;
