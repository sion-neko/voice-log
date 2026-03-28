import { useState } from 'react'
import './App.css'

function App() {
  const [data, setData] = useState(null);
  const [file, setFile] = useState<File | null>(null); 

  const onChangeFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files; 
    if (files && files[0]) {
      setFile(files[0]); 
    } 
  }; 

  const onClickSubmit = async () => {
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch("http://localhost:8000/summarize", {
      method: "POST",
      body: formData,
    });
    const json = await res.json();
    setData(json);
  };

  const callApi = async () => {
    const formData = new FormData();
    formData.append("file", "./input/audio.wav");
    const res = await fetch("http://localhost:8000/summarize", {
      method: "POST",
      body: formData,
    });
    const json = await res.json();
    setData(json);
  };

  return (
    <>
      <div className="App">
        <div className="App-form">
          <input name="file" type="file" accept="audio/*" onChange={onChangeFile} />
          <input type="button" disabled={!file} value="送信" onClick={onClickSubmit} /> 
          <pre style={{ textAlign: "left" }}>
            {JSON.stringify(data, null, 2)}
          </pre>
        </div>
      </div>
    </>
  )
}

export default App
