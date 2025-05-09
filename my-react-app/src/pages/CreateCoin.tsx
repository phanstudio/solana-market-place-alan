import React, { useState } from 'react'

// import Hero from '../components/landingPage/hero'

function CreateCoin() {
    const [preview, setPreview] = useState<string | null>(null);

    const handleImageChange = (e) => {
        const file = e.target.files[0];
        if (file && file.type.startsWith('image/')) {
            setPreview(URL.createObjectURL(file));
        }
    };
    return (
        <div className='relative'>
            <div className="h-64 z-10 crtGradient background-container  top-10 left-10  ...">
                <div className="h-40  justify-center...">
                    <div className="flex flex-col items-center justify-center h-full">
                        <h1 className="text-4xl font-bold ">Launch a new Project</h1>
                        <p className="text-md text-center font-semibold text-sm  w-80 mt-2">Build your reputation in the Web3 ecosystem as you bring vision to life on Notty Terminal                                                                                                                                                                                                                                                                                                   </p>
                    </div>

                </div>

            </div>
            <div className=" h-screen bg-indigo-950 "></div>
            <div className="flex justify-center items-center mt-10  absolute left-16 right-16 border-gray-600 border  top-36 h-218 bg-indigo-950 z-10 p-4 text-white">
                <article className="flex  justify-self-end self-start">lwa</article>
                <form method='POST' className="flex flex-col justify-center w-96">

                    <label htmlFor="projectName" className=' mt-8'>Project name</label>
                    <input type="text" name="" id="projectName" className=" border-gray-600    no-background border rounded-md mt-5 h-8" placeholder="Enter your project name" />
                    <label className=" mt-5" htmlFor="projectDesc">Project description</label>
                    <input type="text" name="" id="projectDesc" className=" border-gray-600   no-background border rounded-md mt-5 h-8" placeholder="Describe your projects" />
                    <label htmlFor="image" className="mt-5">Image</label>
                    <div className="">
                        <input type="file"
                            accept="image/*"
                            onChange={handleImageChange}
                            className="mt-5"
                            id="image" />
                    </div>

                    <label htmlFor="webAddress" className=" border-gray-600 mt-5 h-6">Website Address</label>
                    <input type="text" name="" id="webAddress" className=" border-gray-600   no-background border rounded-md mt-5 h-8" placeholder="Add website Address" />
                    <label htmlFor="twithand" className=" border-gray-600 mt-5 h-6">Twitter Handle</label>
                    <input type="text" name="" id="twithand" className=" border-gray-600   no-background border rounded-md mt-5 h-8" placeholder="Add your twitter handle" />
                    <label htmlFor="discord" className=" border-gray-600 mt-5 h-6">Discord Channel</label>
                    <input type="text" name="" id="discord" className=" border-gray-600  no-background border rounded-md  mt-5 h-8" placeholder="Add your discord address" />
                    <button className=" mt-5 w-32 p-2 rounded-md bg-violet-600">Preview</button>
                </form>

            </div>


        </div>
    )
}

export default CreateCoin