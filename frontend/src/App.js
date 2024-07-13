import React, { useState, useEffect } from 'react';
import { Button, Container, Form, Row, Col, Table } from 'react-bootstrap';
import axios from 'axios';
import FileUploader from './components/fileUploader';

const App = () => {
  const [user, setUser] = useState(null);
  const [spreadsheets, setSpreadsheets] = useState([]);
  const [newSpreadsheetTitle, setNewSpreadsheetTitle] = useState('');
  const [isDisabled, setIsDisabled] = useState(true)
  
  useEffect(() => {
    // Fetch user data if logged in
    const fetchUserData = async () => {
      try {
        const res = await axios.get('http://localhost:5000/user_data', { withCredentials: true });
        console.log(res.data);
        setUser(res.data);
        fetchSpreadsheets();
      } catch (error) {
        console.error('Error fetching user data:', error);
      }
    };

    if (newSpreadsheetTitle.length > 0) setIsDisabled(false);
    else setIsDisabled(true);

    fetchUserData();
  }, [newSpreadsheetTitle]);

  const fetchSpreadsheets = async () => {
    // Fetch existing spreadsheets
    try {
      const res = await axios.get('http://localhost:5000/spreadsheets', { withCredentials: true });
      console.log(res)
      setSpreadsheets(res.data);
    } catch (error) {
      console.error('Error fetching spreadsheets:', error);
    }
  };

  const handleCreateSpreadsheet = async () => {
    // Create new spreadsheet
    try {
      const res = await axios.post('http://localhost:5000/create_spreadsheet', {
        title: newSpreadsheetTitle
      }, { withCredentials: true });
      console.log('Created spreadsheet:', res.data);
      fetchSpreadsheets(); // Refresh spreadsheet list after creation
      setNewSpreadsheetTitle(''); // Clear input field
    } catch (error) {
      console.error('Error creating spreadsheet:', error);
    }
  };

  const handleSpreadsheetLinkClick = (url) => {
    window.open(url, '_blank');
  };

  const handleSignOut = async () => {
    try {
      await axios.get('http://localhost:5000/logout');
      setUser(null); // Clear user state
    } catch (error) {
      console.error('Error signing out:', error);
    }
  };

  return (
    <Container>
      {user && (
        <div className="text-center py-3">
          <div className="d-flex justify-content-end mb-3">
            <Button variant="outline-secondary" onClick={handleSignOut}>
              Sign Out
            </Button>
          </div>
          <h2>Welcome, {user.name}</h2>
          <Table striped bordered hover>
            <thead>
              <tr>
                <th>Title</th>
                <th>Date Created</th>
                <th>Spreadsheet Link</th>
              </tr>
            </thead>
            <tbody>
              {spreadsheets.map((spreadsheet, index) => (
                <tr key={index}>
                  <td>{spreadsheet.title}</td>
                  <td>{new Date(spreadsheet.date_created).toLocaleDateString()}</td>
                  <td>
                    <Button variant="link" onClick={() => handleSpreadsheetLinkClick(spreadsheet.url)}>
                      Open Spreadsheet
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>

          <hr />

          <Form>
            <Row className="align-items-center">
              <Col xs="auto">
                <Form.Label htmlFor="formTitle" className="mr-sm-2">Title</Form.Label>
              </Col>
              <Col xs="sm">
                <Form.Control
                  type="text"
                  placeholder="Enter spreadsheet title"
                  value={newSpreadsheetTitle}
                  onChange={(e) => setNewSpreadsheetTitle(e.target.value)}
                  className="mr-sm-2"
                />
              </Col>
              <Col xs="auto">
                <Button variant="success"  disabled={isDisabled} onClick={handleCreateSpreadsheet}>
                  Create Spreadsheet
                </Button>
              </Col>
            </Row>
          </Form>

          <hr />

          <h3>Add Data to Spreadsheet</h3>
          <FileUploader spreadsheets={spreadsheets}/>
        </div>
      )}

      {!user && (
        <div className="text-center py-3">
          <Button variant="primary" size='lg' href="http://localhost:5000/authorize">
            Login with Google
          </Button>
        </div>
      )}
    </Container>
  );
};

export default App;
