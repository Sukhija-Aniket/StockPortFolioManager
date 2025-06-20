import React, { useState, useEffect } from 'react';
import { Button, FormLabel, Form, Row, Col } from 'react-bootstrap';
import axios from 'axios';

const FileUploader = ({ onUpload, spreadsheets }) => {
  const REACT_APP_BACKEND_SERVICE = process.env.REACT_APP_BACKEND_SERVICE;
  const [files, setFiles] = useState(null);
  const [status, setStatus] = useState('initial');
  const [uploadTitle, setUploadTitle] = useState('');
  const [spreadsheeturl, setSpreadsheeturl] = useState('');
  const [isDisabled, setIsDisabled] = useState(true);

  useEffect(() => {
    console.log("inside the file uploader use effect");
    setIsDisabled(true);
    setSpreadsheeturl('');
    console.log("here also")
    console.log(files);
    if (files) {
      console.log(spreadsheets)
      for (let sheet in spreadsheets) {
        if (spreadsheets[sheet].title === uploadTitle) {
          setSpreadsheeturl(spreadsheets[sheet].url)
          setIsDisabled(false);
        }
        console.log(spreadsheets[sheet].title)
      }
    }
  }, [files, spreadsheets, uploadTitle]);

  const resetState = () => {
    console.log("reset state for file uploader");
    // setFiles(null);
    setUploadTitle('');
    setTimeout(() => setStatus('initial'), 2000);
  }

  const handleFileChange = (e) => {
    if (status === 'uploading') {
      return;
    }
    setStatus('uploading')
    console.log("handling file change");
    console.log("okay getting updated", e);
    console.log(e.target.files);
    if (e.target.files) {
      console.log("entering here as well");
      setStatus('initial');
      setFiles(e.target.files);
      // e.target.value = null;
    }
  };

  const handleTitleChange = (e) => {
    console.log("handling title change")
    setUploadTitle(e.target.value);
  };
  

  const handleUploadData = async () => {
    console.log("handling upload data")
    if (files && uploadTitle) {
      console.log('Uploading files...');

      const formData = new FormData();
      [...files].forEach((file) => {
        formData.append('file', file);
      });
      formData.append('spreadsheet_id', spreadsheeturl.split('/d/')[1]?.split('/')[0]);
      console.log("okay going great: " + formData.getAll('file').toString());
      try {
        const res = await axios.post(`http://${REACT_APP_BACKEND_SERVICE}/data/upload`, formData, {
          withCredentials: true,
          headers: {
            'Content-Type':'multipart/form-data'
          }
        });

        const data = await res.data;
        // Simulate uploading behavior, assuming files are successfully uploaded
        console.log(data);
        setStatus('success');
        resetState();
        if (typeof onUpload === 'function') {
          onUpload();
        }
      } catch (error) {
        console.error('Error uploading files:', error);
        setStatus('fail');
        resetState();
      }
    }
  };

  return (
    <>
      <Form>
        <Row className="align-items-center">
          <Col xs="auto">
            <input
              type="file"
              id="file"
              multiple
              onChange={handleFileChange}
              style={{ display: 'none' }}
            />
            <Button
              as="label"
              htmlFor="file"
              variant="outline-primary"
              className="mb-2"
            >
              Add CSV files
            </Button>
          </Col>
          <Col xs="auto">
            <FormLabel htmlFor="formTitle" className="mr-sm-2">Title</FormLabel>
          </Col>
          <Col xs="sm">
            <Form.Control
              type="text"
              placeholder="Enter spreadsheet title"
              value={uploadTitle}
              onChange={(e) => handleTitleChange(e)}
              className="mr-sm-2"
            />
          </Col>
          <Col className='d-none'>
            <FormLabel htmlFor="formSpreadsheeturl" className="mr-sm-2">spreadsheeturl</FormLabel>
            <Form.Control
              type="hidden"
              value={spreadsheeturl}
              className="mr-sm-2"
            />
          </Col>
          <Col xs="auto">
            <Button variant="success" disabled={isDisabled} onClick={handleUploadData}>
              Upload Data
            </Button>
          </Col>
        </Row>
      </Form>

      {files && (
        <div className="mt-3">
          {[...files].map((file, index) => (
            <div key={index}>
              <strong>File {index + 1}:</strong> {file.name}
            </div>
          ))}
        </div>
      )}

      <Result status={status} />
    </>
  );
};

const Result = ({ status }) => {
  if (status === 'success') {
    return <p>✅ Uploaded successfully!</p>;
  } else if (status === 'fail') {
    return <p>❌ Upload failed!</p>;
  } else if (status === 'uploading') {
    return <p>⏳ Uploading started...</p>;
  } else {
    return null;
  }
};

export default FileUploader;
