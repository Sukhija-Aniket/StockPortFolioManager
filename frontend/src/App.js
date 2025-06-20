import React, { useState, useEffect } from 'react';
import { Button, Container, Form, Row, Col, Table } from 'react-bootstrap';
import axios from 'axios';
import FileUploader from './components/fileUploader';



const App = () => {
  const REACT_APP_BACKEND_SERVICE = process.env.REACT_APP_BACKEND_SERVICE;
  const [user, setUser] = useState(null);
  const [spreadsheets, setSpreadsheets] = useState([]);
  const [newSpreadsheetTitle, setNewSpreadsheetTitle] = useState('');
  const [isDisabled, setIsDisabled] = useState(true)

  const fetchSpreadsheets = async () => {
    // Fetch existing spreadsheets
    try {
      const res = await axios.get(`http://${REACT_APP_BACKEND_SERVICE}/spreadsheets/`, { withCredentials: true });
      console.log("Spreadsheets: ", res)
      setSpreadsheets(res.data);
    } catch (error) {
      console.error('Error fetching spreadsheets:', error);
    }
  };

  useEffect(() => {
    // Fetch user data if logged in
    const fetchUserData = async () => {
      try {
        const res = await axios.get(`http://${REACT_APP_BACKEND_SERVICE}/auth/user`, { withCredentials: true });
        console.log("Response: ", res.data);
        setUser(res.data);
        fetchSpreadsheets();
      } catch (error) {
        console.error('Error fetching user data:', error);
      }
    };

    if (newSpreadsheetTitle.length > 0) setIsDisabled(false);
    else setIsDisabled(true);

    fetchUserData();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [newSpreadsheetTitle]);

  const handleSyncData = async () => {
    try {
      const res = await axios.post(`http://${REACT_APP_BACKEND_SERVICE}/data/sync`, {
        'spreadsheets': spreadsheets
      }, {
        withCredentials: true,
        headers: {
          'Content-Type': 'application/json'
        }
      });
      const data = await res.data;
      console.log(data);
    } catch (error) {
      console.error('Error syncing data:', error);
    }
  };

  const handleCreateSpreadsheet = async () => {
    // Create new spreadsheet
    try {
      const res = await axios.post(`http://${REACT_APP_BACKEND_SERVICE}/spreadsheets/`, {
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

  const handleDeleteClick = async (spreadsheet_url) => {
    try {
      console.log("Deleting a spreadsheet with spreadsheetId:", spreadsheet_url);
      // Extract spreadsheet ID from URL
      const spreadsheet_id = spreadsheet_url.split('/d/')[1]?.split('/')[0];
      if (!spreadsheet_id) {
        console.error('Invalid spreadsheet URL');
        return;
      }
      
      const res = await axios.delete(`http://${REACT_APP_BACKEND_SERVICE}/spreadsheets/${spreadsheet_id}`, { 
        withCredentials: true 
      });
      console.log('Spreadsheet deleted successfully:', res.data);
        // Optionally, refresh the table or remove the deleted spreadsheet from the state
      fetchSpreadsheets();
    } catch(error) {
      console.error('Error deleting spreadsheet:', error);
    }
  };

  const deleteAllCookies = () => {
    document.cookie.split(';').forEach((c) => {
      document.cookie = c.replace(/^ +/, '').replace(/=.*/, '=;expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/');
    });
  };
  
  const handleSignOut = async () => {
    try {
      localStorage.removeItem('user_id');
      localStorage.removeItem('access_token');
      sessionStorage.removeItem('user_id');
      sessionStorage.removeItem('access_token');
      deleteAllCookies();

      await axios.get(`http://${REACT_APP_BACKEND_SERVICE}/auth/logout`);
      setUser(null); // Clear user state
      setSpreadsheets([]);
      deleteAllCookies();
      
    } catch (error) {
      console.error('Error signing out:', error);
    }
  };

  if (!user) {
    console.log("backend service is:", REACT_APP_BACKEND_SERVICE)
  }

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
                <th>Actions</th>
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
                  <td>
                    <Button variant="danger" onClick={() => handleDeleteClick(spreadsheet.url)}>
                      Delete
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
                <Button variant="success" disabled={isDisabled} onClick={handleCreateSpreadsheet}>
                  Create Spreadsheet
                </Button>
              </Col>
            </Row>
          </Form>

          <hr />

          <h3>Add Data to Spreadsheet</h3>
          <FileUploader spreadsheets={spreadsheets} />

          <hr />
          <div className="text-center py-3">
            <Form onSubmit={(e) => { e.preventDefault(); handleSyncData(); }}>
              <Button variant="primary" size="lg" type="submit">
                Sync All Data
              </Button>
            </Form>
          </div>
        </div>
      )}

      {!user && (
        <div className="text-center py-3">
          <Button variant="primary" size='lg' href={`http://${REACT_APP_BACKEND_SERVICE}/auth/authorize`}>
            Login with Google
          </Button>
        </div>
      )}
    </Container>
  );
};

export default App;
