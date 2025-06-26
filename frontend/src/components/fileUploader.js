import React, { useState, useEffect } from 'react';
import { Button, FormLabel, Form, Row, Col, Alert } from 'react-bootstrap';
import { apiPost } from '../utils/apiUtils';

const FileUploader = ({ spreadsheets, setAlertMessage }) => {
  const [files, setFiles] = useState(null);
  const [uploadTitle, setUploadTitle] = useState('');
  const [spreadsheeturl, setSpreadsheeturl] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    console.log("inside the file uploader use effect");
    setSpreadsheeturl('');
    console.log("here also")
    console.log(files);
    if (files) {
      console.log(spreadsheets)
      for (let sheet in spreadsheets) {
        if (spreadsheets[sheet].title === uploadTitle) {
          setSpreadsheeturl(spreadsheets[sheet].url)
        }
        console.log(spreadsheets[sheet].title)
      }
    }
  }, [files, spreadsheets, uploadTitle]);

  const resetState = () => {
    console.log("reset state for file uploader");
    // setFiles(null);
    setUploadTitle('');
    setSpreadsheeturl('');
    setTimeout(() => setLoading(false), 2000);
  }

  const handleFileChange = (e) => {
    if (loading) {
      return;
    }
    console.log("handling file change");
    console.log("okay getting updated", e);
    console.log(e.target.files);
    if (e.target.files) {
      console.log("entering here as well");
      setFiles(e.target.files);
    }
  };

  const handleTitleChange = (e) => {
    console.log("handling title change")
    setUploadTitle(e.target.value);
  };
  

  const handleAddData = async () => {
    console.log("handling add data")
    if (files && uploadTitle) {
      console.log('Uploading files...');
      setLoading(true);

      const formData = new FormData();
      [...files].forEach((file) => {
        formData.append('file', file);
      });
      formData.append('spreadsheet_url', spreadsheeturl);
      formData.append('title', uploadTitle);
      formData.append('spreadsheet_type', 'sheets');
      console.log("okay going great: " + formData.getAll('file').toString());
      
      try {
        const data = await apiPost('/data/add', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });
        
        console.log(data);
        setAlertMessage({ type: 'success', text: 'Data uploaded successfully!' });
        resetState();
      } catch (error) {
        console.error('Error uploading files:', error);
        
        // Handle different types of errors
        if (error.message === 'Authentication required') {
          setAlertMessage({ type: 'danger', text: 'Authentication required' });
        } else {
          setAlertMessage({ type: 'danger', text: 'Failed to upload data. Please try again.' });
        }
      } finally {
        setLoading(false);
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
              disabled={loading}
            />
            <Button
              as="label"
              htmlFor="file"
              variant="outline-primary"
              className="mb-2"
              disabled={loading}
            >
              {loading ? 'Uploading...' : 'Add CSV files'}
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
              disabled={loading}
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
            <Button 
              variant="success" 
              disabled={loading} 
              onClick={handleAddData}
            >
              {loading ? 'Uploading...' : 'Add Data'}
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
    </>
  );
};

export default FileUploader;
