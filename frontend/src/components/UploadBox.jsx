function UploadBox({ file, setFile }) {
  const previewable = file && file.type?.startsWith("image/");
  return (
    <div className="upload-box">
      <label className="upload-label">
        Upload MRI Brain Scan
        <input type="file" accept="image/png,image/jpeg,image/jpg,.dcm,application/dicom" onChange={(e) => setFile(e.target.files?.[0] || null)} />
      </label>
      {file && <div className="preview-area">
        {previewable ? <img src={URL.createObjectURL(file)} alt="MRI Preview" /> : <div className="dicom-preview">DICOM file selected</div>}
        <p>{file.name}</p><small>JPG, PNG, or DICOM • maximum 20 MB</small>
      </div>}
    </div>
  );
}
export default UploadBox;
